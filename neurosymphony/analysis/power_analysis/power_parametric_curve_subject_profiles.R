library(glmmTMB)
library(emmeans)
library(dplyr)
library(ggplot2)

# config
alpha           <- 0.05
boot_seed       <- 1
n_boot_current  <- 1000   # simulations at the current sample size (multiplier = 1)
n_boot_range    <- 1000   # simulations for all other scaled sample sizes

size_multipliers <- c(0.5, 0.75, 1, 1.25, 1.5, 2, 3)

# 1. load data & fit base model
datasetB <- read.csv("/code/music_context_code_cleaned/dataset_categoricalonly.csv", stringsAsFactors = TRUE)
datasetB$track_number <- as.factor(datasetB$track_number)
datasetB$aff_cond     <- datasetB$aggregated_condition_affective

mymodel_allB <- glmmTMB(track_q2_1 ~ aff_cond * aggregated_condition_injected +
                          (1 | userid) +
                          (1 | track_id),
                        data = datasetB, REML = TRUE)

# Extract true parametric parameters
beta     <- fixef(mymodel_allB)$cond
vc       <- VarCorr(mymodel_allB)
sd_user  <- attr(vc$cond$userid, "stddev")
sd_track <- attr(vc$cond$track_id, "stddev")
sd_resid <- sigma(mymodel_allB)

n_subj_orig <- length(unique(datasetB$userid))

subject_profiles <- split(
  datasetB[, c("track_id", "aff_cond", "aggregated_condition_injected")],
  datasetB$userid
)

# 2. helpers

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

# 3. parametric simulation curve
term_labels <- c("aff_cond", "aggregated_condition_injected", "aff_cond:aggregated_condition_injected")
power_curve_list <- list()

for (m in seq_along(size_multipliers)) {
  mult <- size_multipliers[m]
  n_sub <- round(n_subj_orig * mult)
  sims_to_run <- if (mult == 1) n_boot_current else n_boot_range

  cat(sprintf("Multiplier %.2f | Subj: %d | Sims: %d\n", mult, n_sub, sims_to_run))
  set.seed(boot_seed + round(mult * 100))

  pmat       <- matrix(NA, nrow = sims_to_run, ncol = 3, dimnames = list(NULL, term_labels))
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

    pmat[i, ] <- jt$p.value[match(term_labels, jt[[1]])]
  }

  power_curve_list[[m]] <- data.frame(
    multiplier     = mult,
    n_subjects     = n_sub,
    n_observations = round(mean(obs_counts)),
    term           = term_labels,
    power          = colMeans(pmat < alpha, na.rm = TRUE),
    n_converged    = sum(complete.cases(pmat)),
    n_boot         = sims_to_run
  )
}

power_curve_df <- do.call(rbind, power_curve_list)

# 4. plot
power_curve_plot <- ggplot(power_curve_df, aes(x = n_subjects, y = power, color = term, group = term)) +
  geom_hline(yintercept = 0.8, linetype = "dashed", colour = "grey40") +
  geom_line(linewidth = 1) +
  geom_point(size = 2) +
  scale_y_continuous(limits = c(0, 1), labels = scales::percent) +
  labs(x = "Number of participants (per-participant track count follows the real dropout pattern)",
       y = "Estimated Power",
       color = "Fixed-effect term",
       title = "Parametric Power Curve by Sample Size (real dropout pattern preserved)") +
  theme_classic() +
  theme(
    legend.position    = c(0.75, 0.25),
    legend.background  = element_rect(fill = alpha("white", 0.7), colour = "black"),
    legend.title       = element_text(size = 12),
    legend.text        = element_text(size = 10),
    axis.title         = element_text(size = 12),
    axis.text          = element_text(size = 10)
  )

print(power_curve_plot)

fig_dir <- file.path("/code/music_context_code_cleaned", "analysis", "figures")
dir.create(fig_dir, showWarnings = FALSE, recursive = TRUE)
ggsave(file.path(fig_dir, "power_curve_parametric_subject_profiles.png"), power_curve_plot, width = 7, height = 5)

print(power_curve_df)