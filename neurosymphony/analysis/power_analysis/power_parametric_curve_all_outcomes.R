library(glmmTMB)
library(emmeans)
library(dplyr)
library(ggplot2)

# config
alpha           <- 0.05
boot_seed       <- 1
n_boot_current  <- 1000   # simulations at the current sample size (multiplier = 1)
n_boot_range    <- 1000   # simulations for all other scaled sample sizes

size_multipliers <- c(0.5, 0.75, 1, 1.25, 1.5, 2)

parse_bool_arg <- function(name, default) {
  hit <- grep(paste0("^--", name, "="), commandArgs(trailingOnly = TRUE), value = TRUE)
  if (length(hit) == 0) return(default)
  toupper(sub(paste0("^--", name, "="), "", hit[1])) %in% c("TRUE", "T", "1", "YES")
}
run_curve <- parse_bool_arg("curve", TRUE)
if (!run_curve) {
  size_multipliers <- c(1)
}

script_path <- sub("--file=", "", grep("--file=", commandArgs(trailingOnly = FALSE), value = TRUE))
script_dir <- if (length(script_path) > 0) dirname(normalizePath(script_path)) else getwd()
repo_root <- dirname(dirname(script_dir))
data_dir <- if (file.exists(file.path(repo_root, "preprocessing", "dataset.csv"))) {
  file.path(repo_root, "preprocessing")
} else {
  repo_root
}
fig_dir  <- file.path(repo_root, "analysis", "figures")
dir.create(fig_dir, showWarnings = FALSE, recursive = TRUE)

outcomes <- list(
  pos  = list(dv = "track_q2_1", label = "Perceived Positive Emotion Intensity"),
  neg  = list(dv = "track_q2_2", label = "Perceived Negative Emotion Intensity"),
  link = list(dv = "track_q3_1", label = "Perceived Link With Description")
)

# 1. data
dataset <- read.csv(file.path(data_dir, "dataset.csv"), stringsAsFactors = TRUE)
dataset$track_number <- as.factor(dataset$track_number)
dataset$aff_cond <- dataset$description_score_mvt_valence

dataset_onlypos <- read.csv(file.path(data_dir, "dataset_categoricalonly.csv"), stringsAsFactors = TRUE)
dataset_onlypos$track_number <- as.factor(dataset_onlypos$track_number)
dataset_onlypos$aff_cond <- dataset_onlypos$aggregated_condition_affective

model_types <- list(
  categorical = list(data = dataset_onlypos, label = "Categorical (aggregated_condition_affective)"),
  continuous  = list(data = dataset,         label = "Continuous (description_score_mvt_valence)")
)

# 2. helpers

# Builds a synthetic n_subjects design by resampling whole real subject
# profiles (their actual observed rows), with replacement.
generate_design_skeleton <- function(subject_profiles, n_subjects) {
  profile_ids <- sample(names(subject_profiles), n_subjects, replace = TRUE)

  rows <- vector("list", n_subjects)
  for (k in seq_len(n_subjects)) {
    block <- subject_profiles[[profile_ids[k]]]
    block$userid <- paste0("S", k)
    rows[[k]] <- block
  }
  design <- do.call(rbind, rows)

  design$userid   <- factor(design$userid)
  design$track_id <- factor(design$track_id)
  design
}

# Simulates a response under the fitted mixed-model parameters
simulate_parametric_response <- function(skeleton_df, beta, sd_user, sd_track, sd_resid) {
  X <- model.matrix(~ aff_cond * aggregated_condition_injected, data = skeleton_df)
  X <- X[, names(beta), drop = FALSE]
  mu_fixed <- as.numeric(X %*% beta)

  re_subj <- rnorm(nlevels(skeleton_df$userid),   0, sd_user)
  re_item <- rnorm(nlevels(skeleton_df$track_id), 0, sd_track)

  mu_subj <- re_subj[as.integer(skeleton_df$userid)]
  mu_item <- re_item[as.integer(skeleton_df$track_id)]
  eps     <- rnorm(nrow(skeleton_df), 0, sd_resid)

  mu_fixed + mu_subj + mu_item + eps
}

# Runs the full multiplier for one combination,
run_power_curve <- function(dv, data, term_of_interest = "aff_cond") {
  form_fit <- reformulate(
    c("aff_cond * aggregated_condition_injected", "(1 | userid)", "(1 | track_id)"),
    response = dv
  )
  base_model <- glmmTMB(form_fit, data = data, REML = TRUE)

  beta     <- fixef(base_model)$cond
  vc       <- VarCorr(base_model)
  sd_user  <- attr(vc$cond$userid, "stddev")
  sd_track <- attr(vc$cond$track_id, "stddev")
  sd_resid <- sigma(base_model)

  subject_profiles <- split(
    data[, c("track_id", "aff_cond", "aggregated_condition_injected")],
    data$userid
  )
  n_subj_orig <- length(unique(data$userid))

  curve_list <- list()
  for (m in seq_along(size_multipliers)) {
    mult <- size_multipliers[m]
    n_sub <- round(n_subj_orig * mult)
    sims_to_run <- if (mult == 1) n_boot_current else n_boot_range

    cat(sprintf("  Multiplier %.2f | Subj: %d | Sims: %d\n", mult, n_sub, sims_to_run))
    set.seed(boot_seed + round(mult * 100))

    pvec       <- rep(NA_real_, sims_to_run)
    obs_counts <- integer(sims_to_run)

    for (i in 1:sims_to_run) {
      skeleton <- generate_design_skeleton(subject_profiles, n_sub)
      obs_counts[i] <- nrow(skeleton)
      skeleton$sim_response <- simulate_parametric_response(skeleton, beta, sd_user, sd_track, sd_resid)

      fit <- tryCatch(
        glmmTMB(sim_response ~ aff_cond * aggregated_condition_injected +
                  (1 | userid) + (1 | track_id), data = skeleton, REML = TRUE),
        error = function(e) NULL)
      if (is.null(fit)) next

      jt <- tryCatch(as.data.frame(joint_tests(fit)), error = function(e) NULL)
      if (is.null(jt)) next

      pvec[i] <- jt$p.value[match(term_of_interest, jt[[1]])]
    }

    curve_list[[m]] <- data.frame(
      multiplier     = mult,
      n_subjects     = n_sub,
      n_observations = round(mean(obs_counts)),
      power          = mean(pvec < alpha, na.rm = TRUE),
      n_converged    = sum(!is.na(pvec)),
      n_boot         = sims_to_run
    )
  }

  do.call(rbind, curve_list)
}

# 3. run all (outcome x model_type) combinations
all_curves <- list()

for (mtype in names(model_types)) {
  data_m  <- model_types[[mtype]]$data
  for (oname in names(outcomes)) {
    if (!run_curve && mtype == "continuous" && oname == "neg") {
      cat("\n=== continuous | Perceived Negative Emotion Intensity (track_q2_2) === SKIPPED (--curve=FALSE, not significant / not reported)\n")
      next
    }
    dv    <- outcomes[[oname]]$dv
    label <- outcomes[[oname]]$label

    cat(sprintf("\n=== %s | %s (%s) ===\n", mtype, label, dv))
    curve_df <- run_power_curve(dv, data_m)
    curve_df$model_type    <- mtype
    curve_df$outcome       <- oname
    curve_df$outcome_label <- label

    all_curves[[paste(mtype, oname, sep = "_")]] <- curve_df
  }
}

power_curve_df <- do.call(rbind, all_curves)
out_csv_name <- if (run_curve) "power_curve_all_outcomes.csv" else "power_reported_effects_currentN.csv"
write.csv(power_curve_df,
          file.path(fig_dir, out_csv_name),
          row.names = FALSE)

if (!run_curve) {
  print(power_curve_df)
  quit(save = "no", status = 0)
}

# 4. plots
theme_power <- theme_classic() +
  theme(
    legend.position    = c(0.8, 0.25),
    legend.background  = element_rect(fill = alpha("white", 0.7), colour = "black"),
    legend.title       = element_text(size = 12),
    legend.text        = element_text(size = 10),
    axis.title         = element_text(size = 12),
    axis.text          = element_text(size = 10)
  )

plot_power_by_outcome <- function(df, title, file_path) {
  p <- ggplot(df, aes(x = n_subjects, y = power, color = outcome_label, group = outcome_label)) +
    geom_hline(yintercept = 0.8, linetype = "dashed", colour = "grey40") +
    geom_line(linewidth = 1) +
    geom_point(size = 2) +
    scale_y_continuous(limits = c(0, 1), labels = scales::percent) +
    labs(x = "Number of participants (per-participant track count follows the real dropout pattern)",
         y = "Estimated Power (aff_cond term)",
         color = "Outcome",
         title = title) +
    theme_power

  ggsave(file_path, p, width = 7, height = 5)
  p
}

p_categorical <- plot_power_by_outcome(
  power_curve_df %>% filter(model_type == "categorical"),
  "Parametric Power Curve, Categorical Coherence Effect (all three outcomes)",
  file.path(fig_dir, "power_curve_categorical_by_outcome.png")
)

p_continuous <- plot_power_by_outcome(
  power_curve_df %>% filter(model_type == "continuous"),
  "Parametric Power Curve, Continuous Valence Effect (all three outcomes)",
  file.path(fig_dir, "power_curve_continuous_by_outcome.png")
)

print(p_categorical)
print(p_continuous)
print(power_curve_df)
