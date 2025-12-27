clear all; clc;
df = read_and_clean_table("code/merged_exp_data.csv", 0, 3);
dir_rows = [];

response_title = {"Joyful","Sad"};

outdir = fullfile(pwd, 'plots_out');  % change if you want another folder
if ~exist(outdir, 'dir'), mkdir(outdir); end
dpi = 300;         % 300 dpi is print-quality
imgfmt = 'png';    % 'png' is good for raster; consider 'pdf' for vector
figSize = [100 100 1700 900];  % [left bottom width height] in pixels

fs_axes   = 18;   % tick labels
fs_label  = 22;   % x/y labels
fs_title  = 24;   % panel titles
fs_legend = 18;   % legend
fs_super  = 26;   % sgtitle

for expid = 1:2 % symphony id
    for tracknumber = 1:4 % mvt id
        if (expid == 1 && tracknumber == 3) || (expid == 2 && tracknumber == 2)
            continue
        end
        newplot = 1;
        figAvg = figure('Color','w','Name',sprintf('Welch t — Exp %d | Movement %d',expid,tracknumber), ...
                'Units','pixels','Position',figSize);
        set(figAvg, 'DefaultAxesFontSize', fs_axes, ...
            'DefaultTextFontSize', fs_axes);
        tlAvg = tiledlayout(figAvg, 2, 1, 'TileSpacing','compact','Padding','compact');

        for affective = 3:4 % happy or sad measurments
            resp_label = response_title{affective-2};   % 3 -> "Joyful", 4 -> "Sad"
            resp_label = "";
            baseTitle  = sprintf('Exp %d | Movement %d | Feedback: %s', expid, tracknumber, resp_label);

            affcoher = df(df.aggregated_condition_affective=="Aff Coher" & (df.track_number == tracknumber) & contains(df.expid,"exp" + expid),:);
            affopp = df(df.aggregated_condition_affective=="Aff Opp" & (df.track_number == tracknumber) & contains(df.expid,"exp" + expid),:);

            a = min(cellfun(@(x) size(x,1), affopp.data));
            b = min(cellfun(@(x) size(x,1), affcoher.data));

            opphappy = cellfun(@(x) x(1:min(a,b), affective), affopp.data, 'UniformOutput', false);
            coherhappy = cellfun(@(x) x(1:min(a,b), affective), affcoher.data, 'UniformOutput', false);
            X_opp   = cell2mat(opphappy');     % [N x M]
            X_coher = cell2mat(coherhappy');   % [N x M]

            [N, M_opp]   = size(X_opp);
            [~, M_coher] = size(X_coher);

            t = (1:N)';

            % Averages (across subjects)
            avg_opp   = mean(X_opp,   2, 'omitnan');
            avg_coher = mean(X_coher, 2, 'omitnan');

            sem_opp   = std(X_opp,   0, 2, 'omitnan') ./ sqrt(M_opp);
            sem_coher = std(X_coher, 0, 2, 'omitnan') ./ sqrt(M_coher);

            % ---- Plotting ----
            figButter = figure('Color','w','Name',sprintf('Butterflies — %s | %s',baseTitle,resp_label), ...
                   'Units','pixels','Position',figSize);
            set(figButter, 'DefaultAxesFontSize', fs_axes, ...
               'DefaultTextFontSize', fs_axes);
            % figButter = figure('Color','w', ...
            %     'Name', sprintf('Butterflies — %s | %s', baseTitle, resp_label));

            tlButter = tiledlayout(figButter, 2, 2, 'TileSpacing','compact','Padding','compact');

            % 1) Butterfly: OPP
            ax1 = nexttile(tlButter);
            plot(ax1, t, X_opp, 'Color', [0.75 0.85 1], 'LineWidth', 0.8); hold(ax1, 'on');
            fill(ax1, [t; flipud(t)], [avg_opp - sem_opp; flipud(avg_opp + sem_opp)], ...
                [0.4 0.6 1], 'FaceAlpha', 0.2, 'EdgeColor', 'none');
            plot(ax1, t, avg_opp, 'Color', [0 0.2 0.8], 'LineWidth', 2);
            title(ax1, sprintf('Opp %s — N=%d timepts, M=%d subjects', resp_label, N, M_opp), 'FontSize', fs_title);
            xlabel(ax1, 'Time', 'FontSize', fs_label); ylabel(ax1, 'Value (0/1)', 'FontSize', fs_label);
            grid(ax1, 'on'); box(ax1, 'off');

            % 2) Butterfly: COHER
            ax2 = nexttile(tlButter);
            plot(ax2, t, X_coher, 'Color', [1 0.85 0.75], 'LineWidth', 0.8); hold(ax2, 'on');
            fill(ax2, [t; flipud(t)], [avg_coher - sem_coher; flipud(avg_coher + sem_coher)], ...
                [1 0.55 0.2], 'FaceAlpha', 0.2, 'EdgeColor', 'none');
            plot(ax2, t, avg_coher, 'Color', [0.85 0.3 0], 'LineWidth', 2);
            title(ax2, sprintf('Coher %s — N=%d timepts, M=%d subjects', resp_label, N, M_coher), 'FontSize', fs_title);
            xlabel(ax2, 'Time','FontSize', fs_label); ylabel(ax2, 'Value (0/1)','FontSize', fs_label); grid(ax2, 'on'); box(ax2, 'off');

            % 3) Averages overlaid (wide bottom panel spanning two columns)
            ax3 = nexttile(tlButter, [1 2]);
            plot(ax3, t, avg_opp,   'Color', [0 0.2 0.8], 'LineWidth', 2); hold(ax3, 'on');
            plot(ax3, t, avg_coher, 'Color', [0.85 0.3 0], 'LineWidth', 2);


            % Difference on the right y-axis
            yyaxis(ax3, 'right');
            plot(ax3, t, avg_coher - avg_opp, '--', 'LineWidth', 1.5);
            ylabel(ax3, 'Avg(Coher) - Avg(Opp)');

            yyaxis(ax3, 'left');
            ylabel(ax3, 'Average (proportion of 1s)', 'FontSize', fs_label);
            xlabel(ax3, 'Time', 'FontSize', fs_label); grid(ax3, 'on'); box(ax3, 'off');
            lg = legend(ax3, {'Opp avg','Coher avg','Difference'}, 'Location','best');
            lg.FontSize = fs_legend;
            title(ax3, sprintf('Average Comparison %s', resp_label), 'FontSize', fs_title);
            sg = sgtitle(figButter, sprintf('Butterflies — %s | %s', baseTitle, resp_label));
            sg.FontSize = fs_super;

            t = (1:size(X_opp,1))';             % or your real time vector

            alpha = 0.01;       % family-wise error rate
            nPerm = 5000;       % permutations for the null (increase for stability)
            rng(1);             % reproducibility

            [N, M1] = size(X_opp);
            [~, M2] = size(X_coher);

            % Sanity checks
            if size(X_coher,1) ~= N
                error('X_opp and X_coher must have the SAME number of timepoints (rows).');
            end
            if M1 < 2 || M2 < 2
                error('Need at least 2 subjects per condition for Welch t.');
            end

            %% --- Independent-samples (Welch) cluster permutation (default path) ---
            [sig_timepoints, sig_mask_cl] = ...
                cluster_perm_indep_welch(X_opp, X_coher, alpha, nPerm);

            resp_label = response_title{affective-2};   % "Joyful"/"Sad"
            mask = sig_timepoints ~= 0;                  % logical mask of pointwise sig

            if any(mask)
                yyaxis(ax3, 'left');
                hold(ax3, 'on');
            
                % Get current y-limits and place the stars at the bottom
                yl = ylim(ax3);
                yStar = yl(1) * ones(sum(mask), 1);  % at bottom of the panel
            
                scatter(ax3, t(mask), yStar, 120, 'k', 'Marker', '*', ...
                    'DisplayName', 'Sig. timepoints');

                % Average each subject over ONLY the significant timepoints
                subj_opp  = mean(X_opp(mask,:),  1, 'omitnan');   % 1 x M1
                subj_coh  = mean(X_coher(mask,:),1, 'omitnan');   % 1 x M2

                % One-sided Welch t-test matching your directional hypotheses
                switch resp_label
                    case "Joyful"
                        tail = 'right';   % H1: Coherent > Opposite
                    case "Sad"
                        tail = 'left';    % H1: Coherent < Opposite
                end
                [~, p_dir, ~, stats] = ttest2(subj_coh, subj_opp, 'Vartype','unequal', 'Tail', tail);

                % Directional mean difference (Coher - Opp)
                m_coh = mean(subj_coh, 'omitnan');
                m_opp = mean(subj_opp, 'omitnan');
                diff_mean = m_coh - m_opp;

                % Hedges' g (unbiased standardized difference)
                n1 = numel(subj_coh); n2 = numel(subj_opp);
                s1 = std(subj_coh, 0, 'omitnan'); s2 = std(subj_opp, 0, 'omitnan');
                d  = (m_coh - m_opp) / sqrt( (s1^2 + s2^2)/2 );
                J  = 1 - 3/(4*(n1+n2)-9);           % small-sample correction
                g  = d * J;

                % Simple success flag: does the observed direction match the hypothesis?
                expect_sign = strcmp(resp_label,"Joyful") * 1 + strcmp(resp_label,"Sad") * -1; % +1 or -1
                meets_direction = sign(diff_mean) == expect_sign;

                % Proportion of sig timepoints where group averages align with hypothesis
                avg_diff_trace = avg_coher - avg_opp;              % timewise averages
                prop_aligned = mean( (expect_sign== 1 & avg_diff_trace(mask) > 0) | ...
                    (expect_sign==-1 & avg_diff_trace(mask) < 0) );

                % Collect row
                row = struct( ...
                    'expid', expid, ...
                    'movement', tracknumber, ...
                    'response', string(resp_label), ...
                    'n_sig_timepoints', sum(mask), ...
                    'mean_coher', m_coh, ...
                    'mean_opp',   m_opp, ...
                    'mean_diff_coher_minus_opp', diff_mean, ...
                    'tstat_welch', stats.tstat, ...
                    'p_one_sided', p_dir, ...
                    'hedges_g', g, ...
                    'meets_direction', meets_direction, ...
                    'prop_timepoints_aligned', prop_aligned ...
                    );
            else
                % No pointwise significant timepoints to check
                row = struct( ...
                    'expid', expid, ...
                    'movement', tracknumber, ...
                    'response', string(resp_label), ...
                    'n_sig_timepoints', 0, ...
                    'mean_coher', NaN, ...
                    'mean_opp',   NaN, ...
                    'mean_diff_coher_minus_opp', NaN, ...
                    'tstat_welch', NaN, ...
                    'p_one_sided', NaN, ...
                    'hedges_g', NaN, ...
                    'meets_direction', false, ...
                    'prop_timepoints_aligned', NaN ...
                    );
            end


            dir_rows = [dir_rows; row]; %#ok<AGROW>

            %% Plot curves + significant clusters

            analyses = {sig_timepoints, sig_mask_cl};

            % Compute common y-limits across both series so panels are comparable
            ymin = min([avg_opp(:); avg_coher(:)]);
            ymax = max([avg_opp(:); avg_coher(:)]);
            yrng = [ymin ymax];

            ax = nexttile(tlAvg, affective-2);  % 1 = Joyful row, 2 = Sad row
            hold(ax, 'on');

            % Plot the two curves
            hOpp   = plot(ax, t, avg_opp,   'Color', [0 0.2 0.8], 'LineWidth', 2, 'DisplayName', 'Opp avg');
            hCoher = plot(ax, t, avg_coher, 'Color', [0.85 0.3 0], 'LineWidth', 2, 'DisplayName', 'Coher avg');
            % fill(ax, [t; flipud(t)], [avg_opp - sem_opp; flipud(avg_opp + sem_opp)], ...
            %     [0.4 0.6 1], 'FaceAlpha', 0.2, 'EdgeColor', 'none');
            % fill(ax, [t; flipud(t)], [avg_coher - sem_coher; flipud(avg_coher + sem_coher)], ...
            %     [1 0.55 0.2], 'FaceAlpha', 0.2, 'EdgeColor', 'none');
            ylim(ax, yrng);

            % Shade significant time windows for this analysis
            sig_blocks = find_clusters(analyses{1});
            yl = ylim(ax);
            for i = 1:numel(sig_blocks)
                idx = sig_blocks{i};
                patch(ax, [t(idx(1)) t(idx(end)) t(idx(end)) t(idx(1))], ...
                    [yl(1) yl(1) yl(2) yl(2)], ...
                    [0.6 0.9 0.6], 'FaceAlpha', 0.25, 'EdgeColor', 'none', ...
                    'HandleVisibility','off');
                patch(ax3, [t(idx(1)) t(idx(end)) t(idx(end)) t(idx(1))], ...
                    [yl(1) yl(1) yl(2) yl(2)], ...
                    [0.6 0.9 0.6], 'FaceAlpha', 0.25, 'EdgeColor', 'none', ...
                    'HandleVisibility','off');
            end
            hSig = patch(ax, [NaN NaN NaN NaN], [NaN NaN NaN NaN], [0.6 0.9 0.6], ...
                'FaceAlpha',0.25, 'EdgeColor','none', 'Visible','off', ...
                'DisplayName','Significant timepoints');

            % Keep lines on top of patches
            uistack(findobj(ax,'Type','line'),'top');
            grid(ax, 'on'); box(ax, 'off');
            xlabel(ax, 'Time');
            ylabel(ax, 'Average Responses');

            if affective == 3
                legend(ax, [hOpp hCoher hSig], {'Opp avg','Coher avg','Significant timepoints'}, 'Location','best');
            end

            title(ax, "Welch t-Test — "  + baseTitle);

            newplot = 0;

            %% Print cluster table
            fprintf('\n=== %s ===\n', baseTitle);
            if isempty(find(sig_mask_cl))
                fprintf('No supra-threshold clusters found.\n');
            else
                sig_blocks = find_clusters(sig_mask_cl);
                fprintf('Observed clusters:\n');
                for i = 1:numel(clusters_obs)
                    idx = clusters_obs{i};
                    fprintf('  #%d: t=%d..%d (size=%d), p_cluster=%.4f %s\n', ...
                        i, idx(1), idx(end), numel(idx), cluster_pvals(i), ...
                        ternary(any(sig_blocks_match(idx, sig_blocks)),'**SIG**',''));
                end
                fprintf('Cluster-size critical kcrit = %.1f (%.0fth pct of null)\n', ...
                    kcrit, round(100*(1-alpha)));
            end
            saveas(figButter,fullfile(outdir, sprintf('Exp%dmvt%d_butt_%s.png',expid,tracknumber,resp_label)))

        end
        sgtitle(figAvg,  sprintf('Welch t — Exp %d | Movement %d',expid,tracknumber)  )
        saveas(figAvg,fullfile(outdir, sprintf('Exp%dmvt_avg.png',expid,tracknumber)))

    end
end

DirSum = struct2table(dir_rows);
DirSum = sortrows(DirSum, {'expid','movement','response'});

disp('=== Directional summary on pointwise significant timepoints ===');
disp(DirSum);

% Save to CSV (optional)
out_csv = fullfile(pwd, 'directional_summary_on_sig_timepoints.csv');
writetable(DirSum, out_csv);
fprintf('Saved directional summary to %s\n', out_csv);

%% ----------------- FUNCTIONS -----------------

function [sig_timepoints, sig_mask_cl] = ...
    cluster_perm_indep_welch(x1, x2, alpha, nPerm)
% X1: N x M1, X2: N x M2
ntimepoints = size(x1,1);

valid_indices = ~(var(x1,0,2,'omitnan')==0 | var(x2,0,2,'omitnan')==0);
X1 = x1(valid_indices,:);
X2 = x2(valid_indices,:);

[N, M1] = size(X1);
[~, M2] = size(X2);

% Observed Welch t at each time
m1 = mean(X1,2,'omitnan');
m2 = mean(X2,2,'omitnan');
v1 = var(X1,0,2,'omitnan');
v2 = var(X2,0,2,'omitnan');

se2 = v1./M1 + v2./M2;
t_obs = (m2 - m1) ./ sqrt(se2);

% Welch-Satterthwaite df
df = (se2.^2) ./ ((v1./M1).^2./(M1-1) + (v2./M2).^2./(M2-1));
df(~isfinite(df) | df <= 0) = min(M1-1, M2-1);

null_perm = 1000;
t_null = zeros(N, null_perm)*nan;
nulldata_base = [X1, X2];
for i = 1:null_perm
    nulldata_base = nulldata_base(:,randperm(size(nulldata_base, 2)));

    m1 = mean(nulldata_base(:,1:M1),2,'omitnan');
    m2 = mean(nulldata_base(:,M1+1:M2),2,'omitnan');
    v1 = var(nulldata_base(:,1:M1),0,2,'omitnan');
    v2 = var(nulldata_base(:,M1+1:M2),0,2,'omitnan');
    se2 = v1./M1 + v2./M2;
    t_null(:,i) = (m2 - m1) ./ sqrt(se2);
end

t_null_max = max(t_null, [], 1);
t_null_min = min(t_null, [], 1);

mask_obs_pos_tmp = t_obs > prctile(t_null_max, (1-alpha/2)*100);
mask_obs_neg_tmp = t_obs < prctile(t_null_min, (alpha/2)*100);
mask_obs_pos = false(ntimepoints, 1);
mask_obs_neg = false(ntimepoints, 1);
mask_obs_pos(valid_indices) = mask_obs_pos_tmp;
mask_obs_neg(valid_indices) = mask_obs_neg_tmp;

% Significant timepoints
sig_timepoints = mask_obs_pos | mask_obs_neg;

[~, p_dir, ~, stats] = ttest2(X1', X2', 'Vartype','unequal');
sig_timepoints_param_unc = false(ntimepoints, 1);
sig_timepoints_param_unc(valid_indices) = p_dir<0.05;

sig_timepoints_indx = find_clusters(mask_obs_pos | mask_obs_neg);
sig_timepoints_indx = find_clusters(sig_timepoints_param_unc);
sig_timepoints = sig_timepoints_param_unc;
obs_sizes_ontimepoints = cellfun(@numel, sig_timepoints_indx);


% Cluster size correction
obs_and_null = [t_obs, t_null];

pvals = tiedrank(obs_and_null, [], 2)/size(obs_and_null, 2);
clust = pvals < 0.001;

obs_sizes_clcorr = {};
for i = 1 : size(obs_and_null, 2)
    cluster_i = find_clusters(clust(:, i));
    obs_sizes_clcorr{i} = cellfun(@numel, cluster_i);
    if isempty(obs_sizes_clcorr{i})
        max_null_sizes(i) = 0;
    else
        max_null_sizes(i) = max(obs_sizes_clcorr{i});
    end
end

% Cluster-size threshold at (1-alpha) of the null
kcrit = prctile(max_null_sizes(2:end), 100*(1-alpha));

% Significant clusters
sig_idx = find(obs_sizes_clcorr{1} >= kcrit);
sig_mask_cl = false(N,1);
% for i = 1:numel(sig_idx)
%     sig_mask_cl(clusters_obs{sig_idx(i)}) = true;
% end

end

function C = find_clusters(mask)
% Return cell array of contiguous true indices from a logical vector
mask = mask(:);
if ~any(mask); C = {}; return; end
d = diff([false; mask; false]);
starts = find(d==1);
ends   = find(d==-1) - 1;
C = arrayfun(@(s,e) (s:e).', starts, ends, 'UniformOutput', false);
end

function out = ternary(cond, a, b)
    if cond, out = a; else, out = b; end
end

function tf = sig_blocks_match(idx, blocks)
    % Helper to tag printed clusters that are significant
    tf = false;
    for k = 1:numel(blocks)
        if idx(1) >= blocks{k}(1) && idx(end) <= blocks{k}(end)
            tf = true; return;
        end
    end
end

function y = getcumsum(x)
    y = cumsum(x);                     % running sum of 1s
    y = y - cummax((~x).*y);           % subtract last value seen at a zero
    y(~x) = 0;                         % keep zeros as zeros
end
