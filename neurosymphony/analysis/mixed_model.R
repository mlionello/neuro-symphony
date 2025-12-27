# ============================================================
# Context manipulation analysis (cleaned + minimal)
# Runs on: onlypos + all datasets
# Outcomes: track_q2_1 (pos intensity), track_q2_2 (neg intensity)
# ============================================================

suppressPackageStartupMessages({
  library(glmmTMB)
  library(emmeans)
  library(dplyr)
  library(ggplot2)
  library(readr)
})

# ---------------------------
# CONFIG: set your file paths
# ---------------------------
PATH_ALL     <- "neurosymphony/data/preprocessed_dataset.csv"
PATH_ONLYPOS <- "neurosymphony/data/preprocessed_onlypos.csv"

OUT_DIR <- "results_context_models"
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

# ---------------------------
# Helpers
# ---------------------------
as_factor_if_present <- function(df, col) {
  if (col %in% names(df)) df[[col]] <- as.factor(df[[col]])
  df
}

pick_track_id_col <- function(df) {
  if ("track_id" %in% names(df)) return("track_id")
  if ("track_number" %in% names(df)) return("track_number")
  stop("No track identifier found (expected track_id or track_number).")
}

is_numericish <- function(x) is.numeric(x) || is.integer(x)

safe_write_csv <- function(x, path) {
  readr::write_csv(as.data.frame(x), path)
}

theme_pub <- function() {
  theme_classic(base_size = 16) +
    theme(
      legend.position = c(0.8, 0.2),
      legend.background = element_rect(fill = scales::alpha("white", 0.7), colour = "black"),
      legend.title = element_text(size = 14),
      legend.text  = element_text(size = 12),
      axis.title   = element_text(size = 14),
      axis.text    = element_text(size = 12)
    )
}

# ---------------------------
# Data loaders
# ---------------------------
load_all_dataset <- function(path) {
  df <- read.csv(path, stringsAsFactors = FALSE)

  # factors commonly used in your code
  df <- as_factor_if_present(df, "userid")
  df <- as_factor_if_present(df, "track_number")
  df <- as_factor_if_present(df, "track_id")
  df <- as_factor_if_present(df, "sign_targetperc")
  df <- as_factor_if_present(df, "aggregated_condition_injected")

  # aff_cond definition for ALL dataset (continuous in your original script)
  if (!("description_score_mvt_valence" %in% names(df))) {
    stop("ALL dataset missing 'description_score_mvt_valence'.")
  }
  df$aff_cond <- df$description_score_mvt_valence

  df
}

load_onlypos_dataset <- function(path) {
  df <- read.csv(path, stringsAsFactors = FALSE)

  df <- as_factor_if_present(df, "userid")
  df <- as_factor_if_present(df, "track_number")
  df <- as_factor_if_present(df, "track_id")
  df <- as_factor_if_present(df, "aggregated_condition_injected")

  # aff_cond definition for ONLYPOS dataset (categorical in your original script)
  if (!("aggregated_condition_affective" %in% names(df))) {
    stop("ONLYPOS dataset missing 'aggregated_condition_affective'.")
  }
  df$aff_cond <- as.factor(df$aggregated_condition_affective)

  df
}

# ---------------------------
# Model + reporting
# ---------------------------
fit_and_report <- function(df, dataset_name, outcome) {
  # checks
  if (!(outcome %in% names(df))) stop(paste0(dataset_name, " missing outcome: ", outcome))
  if (!("aff_cond" %in% names(df))) stop(paste0(dataset_name, " missing aff_cond"))
  if (!("aggregated_condition_injected" %in% names(df))) {
    stop(paste0(dataset_name, " missing 'aggregated_condition_injected'"))
  }

  track_id_col <- pick_track_id_col(df)

  # keep complete cases for relevant vars
  model_df <- df %>%
    mutate(
      aggregated_condition_injected = as.factor(aggregated_condition_injected),
      userid = as.factor(userid),
      track_id_tmp = as.factor(.data[[track_id_col]])
    ) %>%
    filter(
      !is.na(.data[[outcome]]),
      !is.na(aff_cond),
      !is.na(aggregated_condition_injected),
      !is.na(userid),
      !is.na(track_id_tmp)
    )

  # model formula (random intercepts)
  fml <- as.formula(
    paste0(outcome,
           " ~ aff_cond * aggregated_condition_injected + (1|userid) + (1|track_id_tmp)")
  )

  # fit model (Gaussian by default)
  m <- glmmTMB(fml, data = model_df, REML = TRUE)

  tag <- paste(dataset_name, outcome, sep = "__")

  # ---------------------------
  # Stats outputs
  # ---------------------------
  jt <- joint_tests(m)
  safe_write_csv(jt, file.path(OUT_DIR, paste0("joint_tests__", tag, ".csv")))

  emm_main <- emmeans(m, ~ aff_cond)
  safe_write_csv(emm_main, file.path(OUT_DIR, paste0("emmeans_aff_cond__", tag, ".csv")))
  safe_write_csv(pairs(emm_main), file.path(OUT_DIR, paste0("pairs_aff_cond__", tag, ".csv")))

  emm_by_inj <- emmeans(m, ~ aff_cond | aggregated_condition_injected)
  safe_write_csv(emm_by_inj, file.path(OUT_DIR, paste0("emmeans_aff_by_injected__", tag, ".csv")))
  safe_write_csv(pairs(emm_by_inj), file.path(OUT_DIR, paste0("pairs_aff_by_injected__", tag, ".csv")))

  # ---------------------------
  # Plots
  # ---------------------------
  ylab <- if (outcome == "track_q2_1") {
    "Perceived Positive Emotion Intensity"
  } else if (outcome == "track_q2_2") {
    "Perceived Negative Emotion Intensity"
  } else {
    outcome
  }

  # If aff_cond is categorical -> interaction plot with points/CI/lines
  # If aff_cond is numeric -> line + ribbon across observed range and optional slopes
  if (!is_numericish(model_df$aff_cond)) {
    grid <- emmeans(m, ~ aff_cond * aggregated_condition_injected)
    dfp <- as.data.frame(grid)

    p <- ggplot(
      dfp,
      aes(x = aff_cond, y = emmean,
          color = aggregated_condition_injected,
          group = aggregated_condition_injected)
    ) +
      geom_point(position = position_dodge(width = 0.2), size = 3) +
      geom_errorbar(aes(ymin = lower.CL, ymax = upper.CL),
                    position = position_dodge(width = 0.2),
                    width = 0.15) +
      geom_line(position = position_dodge(width = 0.2)) +
      labs(
        x = "Affective condition",
        y = ylab,
        color = "Injected condition"
      ) +
      theme_pub()

    ggsave(
      filename = file.path(OUT_DIR, paste0("plot_interaction__", tag, ".png")),
      plot = p, width = 8, height = 5, dpi = 300
    )

  } else {
    # Continuous aff_cond: prediction curve by injected condition
    cond_seq <- seq(
      from = min(model_df$aff_cond, na.rm = TRUE),
      to   = max(model_df$aff_cond, na.rm = TRUE),
      length.out = 60
    )

    grid <- emmeans(
      m,
      ~ aff_cond | aggregated_condition_injected,
      at = list(aff_cond = cond_seq)
    )
    dfp <- as.data.frame(grid)

    p <- ggplot(
      dfp,
      aes(x = aff_cond, y = emmean,
          color = aggregated_condition_injected,
          fill  = aggregated_condition_injected)
    ) +
      geom_line(linewidth = 1) +
      geom_ribbon(aes(ymin = lower.CL, ymax = upper.CL),
                  alpha = 0.15, colour = NA) +
      labs(
        x = "Description valence (aff_cond)",
        y = ylab,
        color = "Injected condition",
        fill  = "Injected condition"
      ) +
      theme_pub()

    ggsave(
      filename = file.path(OUT_DIR, paste0("plot_curve__", tag, ".png")),
      plot = p, width = 8, height = 5, dpi = 300
    )

    # Optional: simple slopes (interaction interpretation)
    slopes <- emtrends(m, ~ aggregated_condition_injected, var = "aff_cond")
    safe_write_csv(slopes, file.path(OUT_DIR, paste0("slopes_by_injected__", tag, ".csv")))
    safe_write_csv(pairs(slopes), file.path(OUT_DIR, paste0("slopes_by_injected_pairs__", tag, ".csv")))

    # Optional: injected differences at mean +/- SD of aff_cond
    m_aff <- mean(model_df$aff_cond, na.rm = TRUE)
    s_aff <- sd(model_df$aff_cond, na.rm = TRUE)

    emm_inj_at <- emmeans(
      m,
      ~ aggregated_condition_injected | aff_cond,
      at = list(aff_cond = c(m_aff - s_aff, m_aff, m_aff + s_aff))
    )
    safe_write_csv(emm_inj_at, file.path(OUT_DIR, paste0("emmeans_injected_at_m_sd__", tag, ".csv")))
    safe_write_csv(pairs(emm_inj_at), file.path(OUT_DIR, paste0("pairs_injected_at_m_sd__", tag, ".csv")))
  }

  invisible(m)
}

# ---------------------------
# Run everything
# ---------------------------
dataset_all     <- load_all_dataset(PATH_ALL)
dataset_onlypos <- load_onlypos_dataset(PATH_ONLYPOS)

outcomes <- c("track_q2_1", "track_q2_2")

models <- list()
for (dv in outcomes) {
  models[[paste0("all__", dv)]]     <- fit_and_report(dataset_all, "all", dv)
  models[[paste0("onlypos__", dv)]] <- fit_and_report(dataset_onlypos, "onlypos", dv)
}

message("Done. Outputs written to: ", normalizePath(OUT_DIR))
