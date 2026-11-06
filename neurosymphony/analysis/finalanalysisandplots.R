library(glmmTMB)
library(emmeans)
library(optimx)
library(ggplot2)

script_path <- sub("--file=", "", grep("--file=", commandArgs(trailingOnly = FALSE), value = TRUE))
script_dir <- if (length(script_path) > 0) dirname(normalizePath(script_path)) else getwd()
repo_root <- dirname(script_dir)
data_dir <- if (file.exists(file.path(repo_root, "preprocessing", "dataset.csv"))) {
  file.path(repo_root, "preprocessing")
} else {
  repo_root
}
fig_dir  <- file.path(repo_root, "analysis", "figures")
dir.create(fig_dir, showWarnings = FALSE, recursive = TRUE)

# ==============================================================================
# 1. DATA
# ==============================================================================
dataset_continuous <- read.csv(file.path(data_dir, "dataset.csv"), stringsAsFactors = TRUE)
dataset_continuous$track_number <- as.factor(dataset_continuous$track_number)
dataset_continuous$aff_cond <- dataset_continuous$description_score_mvt_valence

dataset_categorical <- read.csv(file.path(data_dir, "dataset_categoricalonly.csv"), stringsAsFactors = TRUE)
dataset_categorical$track_number <- as.factor(dataset_categorical$track_number)
dataset_categorical$aff_cond <- dataset_categorical$aggregated_condition_affective

outcomes <- list(
  pos  = list(dv = "track_q2_1", label = "Felt positive intensity (1–7)"),
  neg  = list(dv = "track_q2_2", label = "Felt negative intensity (1–7)"),
  link = list(dv = "track_q3_1", label = "Text–music linkage (1–5)")
)

# ==============================================================================
# 2. MODEL FITTING
# ==============================================================================
fit_mixed_model <- function(dv, data) {
  form <- reformulate(
    c("aff_cond * aggregated_condition_injected", "(1 || userid)", "(1 || track_id)"),
    response = dv
  )
  glmmTMB(form, data = data, REML = TRUE)
}

mde_80 <- function(se) (qnorm(0.975) + qnorm(0.80)) * se

effect_row <- function(label, model_type, effect, summ, scale = 1) {
  s <- as.data.frame(summ)
  est_col <- intersect(c("estimate", "aff_cond.trend"), names(s))[1]
  est <- s[[est_col]] * scale
  se <- s$SE * scale
  data.frame(outcome = label, model = model_type, effect = effect,
             estimate = est, SE = se,
             lower.CL = est - qnorm(0.975) * se, upper.CL = est + qnorm(0.975) * se,
             MDE_80 = mde_80(se))
}

summarize_categorical_model <- function(model, label) {
  cat("\n---", label, "| categorical (aggregated_condition_affective) ---\n")
  print(joint_tests(model))
  print(emmeans(model, ~ aff_cond))
  print(pairs(emmeans(model, ~ aff_cond)))
  emm_by_injected <- emmeans(model, ~ aff_cond | aggregated_condition_injected)
  print(emm_by_injected)
  print(pairs(emm_by_injected))

  rows <- rbind(
    effect_row(label, "categorical", "Coherent - Opposite",
               summary(pairs(emmeans(model, ~ aff_cond)))),
    effect_row(label, "categorical", "Injected - Reference",
               summary(pairs(emmeans(model, ~ aggregated_condition_injected))))
  )
  print(rows, digits = 3)
  rows
}

summarize_continuous_model <- function(model, data, label) {
  cat("\n---", label, "| continuous (description_score_mvt_valence) ---\n")
  print(joint_tests(model))
  print(emmeans(model, ~ aff_cond))
  print(emmeans(model, ~ aff_cond | aggregated_condition_injected))

  m <- mean(data$aff_cond, na.rm = TRUE)
  s <- sd(data$aff_cond, na.rm = TRUE)

  emm_injected_at_points <- emmeans(
    model, ~ aggregated_condition_injected | aff_cond,
    at = list(aff_cond = c(m - s, m, m + s))
  )
  print(emm_injected_at_points)
  print(pairs(emm_injected_at_points))

  slopes_by_injected <- emtrends(model, ~ aggregated_condition_injected, var = "aff_cond")
  print(slopes_by_injected)
  print(pairs(slopes_by_injected))

  rows <- rbind(
    effect_row(label, "continuous", "Valence slope per SD",
               summary(emtrends(model, ~ 1, var = "aff_cond")), scale = s),
    effect_row(label, "continuous", "Injected - Reference (at mean valence)",
               summary(pairs(emmeans(model, ~ aggregated_condition_injected))))
  )
  print(rows, digits = 3)
  rows
}

# ==============================================================================
# 3. PLOT
# ==============================================================================
as_emm_df <- function(emm_grid) {
  df <- as.data.frame(emm_grid)
  if (!"lower.CL" %in% names(df) && "asymp.LCL" %in% names(df)) {
    df$lower.CL <- df$asymp.LCL
    df$upper.CL <- df$asymp.UCL
  }
  df
}

theme_paper <- function() {
  theme_classic() +
    theme(
      legend.position  = "bottom",
      legend.direction = "horizontal",
      legend.title = element_text(size = 18),
      legend.text  = element_text(size = 16),
      axis.title   = element_text(size = 20),
      axis.text    = element_text(size = 18)
    )
}

series_palette <- function(injected_levels) {
  labels <- c(injected_levels, "Pooled")
  list(
    color = setNames(c("#2a78d6", "#eb6834", "#0b0b0b"), labels),
    shape = setNames(c(16, 17, 18), labels)
  )
}

cond_display   <- c("Aff Coher" = "Coherent", "Aff Opp" = "Opposite")
series_display <- c(Inj = "Injected", Ref = "Reference", Pooled = "Pooled")

offset_series_x <- function(x_factor, series, series_order, spacing = 0.2, right_shift = 0.06) {
  other_offsets <- seq(0, spacing, length.out = length(series_order) - 1) + right_shift
  offsets <- setNames(c(-spacing, other_offsets), series_order)
  offsets <- offsets - mean(offsets)
  as.numeric(x_factor) + offsets[as.character(series)]
}

plot_categorical_means <- function(model, ylab, file_path) {
  emm_df <- as_emm_df(emmeans(model, ~ aff_cond * aggregated_condition_injected))
  emm_df$series <- as.character(emm_df$aggregated_condition_injected)

  pooled_df <- as_emm_df(emmeans(model, ~ aff_cond))
  pooled_df$series <- "Pooled"

  injected_levels <- levels(emm_df$aggregated_condition_injected)
  pal <- series_palette(injected_levels)
  series_order <- c("Pooled", injected_levels)

  plot_df <- rbind(emm_df[, c("aff_cond", "emmean", "lower.CL", "upper.CL", "series")],
                    pooled_df[, c("aff_cond", "emmean", "lower.CL", "upper.CL", "series")])
  plot_df$series <- factor(plot_df$series, levels = series_order)
  plot_df$x_num <- offset_series_x(plot_df$aff_cond, plot_df$series, series_order)

  p <- ggplot(plot_df, aes(x = x_num, y = emmean, color = series, shape = series, group = series)) +
    geom_line(data = ~ subset(., series != "Pooled"), linewidth = 0.8) +
    geom_errorbar(data = ~ subset(., series != "Pooled"), aes(ymin = lower.CL, ymax = upper.CL),
                  width = 0.08, linewidth = 0.8) +
    geom_point(data = ~ subset(., series != "Pooled"), size = 3.5) +
    geom_line(data = ~ subset(., series == "Pooled"), linetype = "dashed", linewidth = 1.3) +
    geom_errorbar(data = ~ subset(., series == "Pooled"), aes(ymin = lower.CL, ymax = upper.CL),
                  width = 0.08, linewidth = 1.3) +
    geom_point(data = ~ subset(., series == "Pooled"), size = 4.5) +
    scale_x_continuous(breaks = seq_along(levels(plot_df$aff_cond)),
                       labels = unname(cond_display[levels(plot_df$aff_cond)]),
                       expand = expansion(add = 0.3)) +
    scale_color_manual(values = pal$color, breaks = names(pal$color),
                       labels = unname(series_display[names(pal$color)])) +
    scale_shape_manual(values = pal$shape, breaks = names(pal$shape),
                       labels = unname(series_display[names(pal$shape)])) +
    labs(y = ylab, x = "Affective condition", color = "Condition", shape = "Condition") +
    theme_paper()

  ggsave(file_path, p, width = 7, height = 5.3)
  p
}

plot_continuous_curve <- function(model, data, ylab, file_path) {
  cond_seq <- seq(min(data$aff_cond, na.rm = TRUE),
                   max(data$aff_cond, na.rm = TRUE), length.out = 50)
  emm_df <- as_emm_df(
    emmeans(model, ~ aff_cond | aggregated_condition_injected, at = list(aff_cond = cond_seq))
  )

  pooled_df <- as_emm_df(emmeans(model, ~ aff_cond, at = list(aff_cond = cond_seq)))
  pooled_df$series <- "Pooled"
  injected_levels <- levels(emm_df$aggregated_condition_injected)
  pal <- series_palette(injected_levels)

  p <- ggplot(emm_df, aes(x = aff_cond, y = emmean,
                          color = aggregated_condition_injected,
                          fill = aggregated_condition_injected)) +
    geom_ribbon(aes(ymin = lower.CL, ymax = upper.CL), alpha = 0.12, colour = NA) +
    geom_line(linewidth = 1) +
    geom_ribbon(data = pooled_df, aes(x = aff_cond, ymin = lower.CL, ymax = upper.CL,
                                       fill = series, color = series),
                alpha = 0.12, linetype = 0, inherit.aes = FALSE) +
    geom_line(data = pooled_df, aes(x = aff_cond, y = emmean, color = series),
              linewidth = 1.3, linetype = "dashed", inherit.aes = FALSE) +
    scale_color_manual(values = pal$color, breaks = names(pal$color),
                       labels = unname(series_display[names(pal$color)])) +
    scale_fill_manual(values = pal$color, breaks = names(pal$color),
                      labels = unname(series_display[names(pal$color)])) +
    labs(x = "Description Valence", y = ylab,
         color = "Condition", fill = "Condition") +
    theme_paper()

  ggsave(file_path, p, width = 7, height = 5.3)
  p
}

plot_low_mid_high <- function(model, data, ylab, file_path) {
  m <- mean(data$aff_cond, na.rm = TRUE)
  s <- sd(data$aff_cond, na.rm = TRUE)
  cond_points <- c(Low = m - s, Mid = m, High = m + s)

  emm_df <- as_emm_df(
    emmeans(model, ~ aff_cond * aggregated_condition_injected,
            at = list(aff_cond = unname(cond_points)))
  )
  emm_df$cond_level <- factor(
    names(cond_points)[match(emm_df$aff_cond, unname(cond_points))],
    levels = c("Low", "Mid", "High")
  )
  emm_df$series <- as.character(emm_df$aggregated_condition_injected)

  lab_low  <- bquote(mu - sigma == .(round(m - s, 2)))
  lab_mid  <- bquote(mu == .(round(m, 2)))
  lab_high <- bquote(mu + sigma == .(round(m + s, 2)))

  pooled_df <- as_emm_df(emmeans(model, ~ aff_cond, at = list(aff_cond = unname(cond_points))))
  pooled_df$cond_level <- factor(
    names(cond_points)[match(pooled_df$aff_cond, unname(cond_points))],
    levels = c("Low", "Mid", "High")
  )
  pooled_df$series <- "Pooled"

  injected_levels <- levels(emm_df$aggregated_condition_injected)
  pal <- series_palette(injected_levels)
  series_order <- c("Pooled", injected_levels)

  plot_df <- rbind(emm_df[, c("cond_level", "emmean", "lower.CL", "upper.CL", "series")],
                    pooled_df[, c("cond_level", "emmean", "lower.CL", "upper.CL", "series")])
  plot_df$series <- factor(plot_df$series, levels = series_order)
  plot_df$x_num <- offset_series_x(plot_df$cond_level, plot_df$series, series_order)

  p <- ggplot(plot_df, aes(x = x_num, y = emmean, color = series, shape = series, group = series)) +
    geom_line(data = ~ subset(., series != "Pooled"), linewidth = 0.8) +
    geom_errorbar(data = ~ subset(., series != "Pooled"), aes(ymin = lower.CL, ymax = upper.CL),
                  width = 0.08, linewidth = 0.8) +
    geom_point(data = ~ subset(., series != "Pooled"), size = 3.5) +
    geom_line(data = ~ subset(., series == "Pooled"), linetype = "dashed", linewidth = 1.3) +
    geom_errorbar(data = ~ subset(., series == "Pooled"), aes(ymin = lower.CL, ymax = upper.CL),
                  width = 0.08, linewidth = 1.3) +
    geom_point(data = ~ subset(., series == "Pooled"), size = 4.5) +
    scale_x_continuous(breaks = seq_along(levels(plot_df$cond_level)),
                        labels = c(lab_low, lab_mid, lab_high),
                        expand = expansion(add = 0.3)) +
    scale_color_manual(values = pal$color, breaks = names(pal$color),
                       labels = unname(series_display[names(pal$color)])) +
    scale_shape_manual(values = pal$shape, breaks = names(pal$shape),
                       labels = unname(series_display[names(pal$shape)])) +
    labs(y = ylab, x = "Description Valence", color = "Condition", shape = "Condition") +
    theme_paper()

  ggsave(file_path, p, width = 7, height = 5.3)
  p
}

# ==============================================================================
# 4. RUN MODELS & PLOTS FOR EACH OUTCOME
# ==============================================================================
models <- list()
effects <- list()

for (name in names(outcomes)) {
  dv    <- outcomes[[name]]$dv
  label <- outcomes[[name]]$label

  m_cat <- fit_mixed_model(dv, dataset_categorical)
  effects[[paste0(name, "_categorical")]] <- summarize_categorical_model(m_cat, label)
  plot_categorical_means(m_cat, label, file.path(fig_dir, paste0(name, "_categorical_means.png")))

  m_cont <- fit_mixed_model(dv, dataset_continuous)
  effects[[paste0(name, "_continuous")]] <- summarize_continuous_model(m_cont, dataset_continuous, label)
  plot_continuous_curve(m_cont, dataset_continuous, label, file.path(fig_dir, paste0(name, "_continuous_curve.png")))
  plot_low_mid_high(m_cont, dataset_continuous, label, file.path(fig_dir, paste0(name, "_low_mid_high.png")))

  models[[paste0(name, "_categorical")]] <- m_cat
  models[[paste0(name, "_continuous")]]  <- m_cont
}

effects <- do.call(rbind, effects)
rownames(effects) <- NULL
write.csv(effects, file.path(fig_dir, "effect_estimates_ci.csv"), row.names = FALSE)

# ==============================================================================
# 5. SENSITIVITY CURVES
# ==============================================================================
sensitivity_power <- function(delta, se, alpha = 0.05) {
  z <- qnorm(1 - alpha / 2)
  pnorm(delta / se - z) + pnorm(-delta / se - z)
}

plot_sensitivity_curves <- function(effects, file_path) {
  rows  <- effects[effects$model == "categorical" & effects$effect == "Coherent - Opposite", ]
  short <- c("Positive intensity", "Negative intensity", "Text-music linkage")
  keys  <- sprintf("%s (80%% at %.2f)", short, rows$MDE_80)

  delta    <- seq(0, 0.8, by = 0.005)
  curve_df <- do.call(rbind, lapply(seq_len(nrow(rows)), function(i)
    data.frame(series = keys[i], delta = delta, power = sensitivity_power(delta, rows$SE[i]))))
  curve_df$series <- factor(curve_df$series, levels = keys)
  mde_df <- data.frame(series = factor(keys, levels = keys), delta = rows$MDE_80, power = 0.80)

  p <- ggplot(curve_df, aes(x = delta, y = power, colour = series, linetype = series, shape = series)) +
    geom_hline(yintercept = 0.80, linetype = "dashed", colour = "grey45", linewidth = 0.6) +
    geom_line(linewidth = 1.1) +
    geom_point(data = mde_df, size = 4) +
    scale_colour_manual(values = setNames(c("#2a78d6", "#eb6834", "#1baf7a"), keys)) +
    scale_linetype_manual(values = setNames(c("solid", "longdash", "dotdash"), keys)) +
    scale_shape_manual(values = setNames(c(16, 17, 15), keys)) +
    scale_x_continuous(breaks = seq(0, 0.8, by = 0.1), expand = expansion(mult = c(0.01, 0.02))) +
    scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, by = 0.2),
                       labels = c("0", ".20", ".40", ".60", ".80", "1.00")) +
    labs(x = "True difference between conditions (scale points)", y = "Power",
         colour = NULL, linetype = NULL, shape = NULL) +
    theme_paper() +
    theme(legend.position = "inside", legend.position.inside = c(0.98, 0.03),
          legend.justification = c(1, 0), legend.direction = "vertical",
          legend.key.width = unit(1.6, "cm"))

  ggsave(file_path, p, width = 7, height = 5.3)
  p
}

plot_sensitivity_curves(effects, file.path(fig_dir, "sensitivity_power_curves.png"))
sens_rows <- effects[effects$model == "categorical" & effects$effect == "Coherent - Opposite", ]
cat("\n--- Sensitivity: power to detect a true Coherent-Opposite difference (scale points) ---\n")
sens_table <- sapply(setNames(sens_rows$SE, sens_rows$outcome),
                     function(se) sensitivity_power(seq(0.1, 0.6, by = 0.1), se))
rownames(sens_table) <- sprintf("delta = %.1f", seq(0.1, 0.6, by = 0.1))
print(round(sens_table, 2))
