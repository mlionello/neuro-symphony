function df = aggregate_aff_inj(df, doplot, reduce)
conditionMappings = containers.Map({
    'aggregated_condition_affective',
    'aggregated_condition_injected',
    'aggregated_condition_affective_only_true',
    'aggregated_condition_affective_only_inj'}, {
    containers.Map({'1', '2', '3', '4'}, {'Aff Coher', 'Aff Opp', 'Aff Coher', 'Aff Opp'}),
    containers.Map({'1', '2', '3', '4'}, {'Ref', 'Ref', 'Inj', 'Inj'}),
    containers.Map({'1', '2', '3', '4'}, {'Group A', 'Group B', 'Group C', 'Group C'}),
    containers.Map({'1', '2', '3', '4'}, {'Group C', 'Group C', 'Group A', 'Group B'})
    });

% Apply mappings
keys = conditionMappings.keys;
for k = 1:length(keys)
    col = keys{k};
    mapping = conditionMappings(col);
    for i = 1:height(df)
        if any(contains(fieldnames(df), "track_condition"))
            key = num2str(df.track_condition(i)); % Convert to string key
        else
            key = num2str(df.cond_track(i)); % Convert to string key
        end
    df.(col)(i) = string(mapping(key));
    end
end

if doplot==1
    plot_mvt_score_dist(df);
end

% Ensure consistent binning
binEdges = linspace(0, 10, 21);

% ===================
% Figure 1: Both inj and ref
% ===================
figure;
t = tiledlayout(2,1,'TileSpacing','compact','Padding','compact');

if ~contains(fieldnames(df), 'track_condition')
    df.track_condition = df.cond_track;
end

nexttile
vals_coh = df.description_valence_mean(ismember(df.track_condition, [1, 3]));
histogram(vals_coh, binEdges, 'FaceAlpha',0.7);
title(sprintf("Affective Coherence (n=%d)", numel(vals_coh)));
xlabel("Description Valence (1-10)");
ylabel("Frequency");
xlim([0 10]);
grid on;

nexttile
vals_opp = df.description_valence_mean(ismember(df.track_condition, [2, 4]));
histogram(vals_opp, binEdges, 'FaceAlpha',0.7);
title(sprintf("Affective Opposite (n=%d)", numel(vals_opp)));
xlabel("Description Valence (1-10)");
ylabel("Frequency");
xlim([0 10]);
grid on;

sgtitle("Description Valence Distribution (Both Injected and Reference)");

% ===================
% Figure 2: Only ref
% ===================
figure;
t = tiledlayout(2,1,'TileSpacing','compact','Padding','compact');

nexttile
vals_coh_ref = df.description_valence_mean(df.track_condition == 1);
histogram(vals_coh_ref, binEdges, 'FaceAlpha',0.7);
title(sprintf("Affective Coherence (Reference Only, n=%d)", numel(vals_coh_ref)));
xlabel("Description Valence (1-10)");
ylabel("Frequency");
xlim([0 10]);
grid on;

nexttile
vals_opp_ref = df.description_valence_mean(df.track_condition == 2);
histogram(vals_opp_ref, binEdges, 'FaceAlpha',0.7);
title(sprintf("Affective Opposite (Reference Only, n=%d)", numel(vals_opp_ref)));
xlabel("Description Valence (1-10)");
ylabel("Frequency");
xlim([0 10]);
grid on;

sgtitle("Description Valence Distribution (Reference Only)");


ref_lower_than_7 = df(ismember(df.track_condition, [1]) & df.description_valence_mean < 7, ["expid","track_number"]);
sad_movements = unique(ref_lower_than_7);
for i = 1:height(sad_movements)
    matching_rows = ref_lower_than_7(string(ref_lower_than_7.expid) == sad_movements.expid{i} & ...
        ref_lower_than_7.track_number == sad_movements.track_number(i), :);
    sad_movements.nb_obs(i) = height(matching_rows);
end

fprintf("lsit of sad movements: \n")
sad_movements

if reduce == 1
    df(df.description_valence_mean < 7 & ismember(df.track_condition, [1, 3]), :) = [];
    df(df.description_valence_mean > 4 & ismember(df.track_condition, [2, 4]), :) = [];
elseif reduce == 2
    % df(df.description_valence_mean < 7 & ismember(df.track_condition, [1, 3]), :) = [];
    threshold = 2;
    for exp_i = 1:8
        expid = "exp" + string(exp_i);
        for track_n = 1:4
            coher_indices = df.aggregated_condition_affective == "Aff Coher";
            opp_indices = df.aggregated_condition_affective == "Aff Opp";
            exp_samples = df.expid == expid;
            track_samples = df.track_number == track_n;
            mvt_samples = track_samples & exp_samples;

            mean_coher = mean(df(mvt_samples & coher_indices, "description_score_mvt_valence").Variables);
            mean_opp = mean(df(mvt_samples & opp_indices, "description_score_mvt_valence").Variables);
            if mean_coher > mean_opp % in the case the coherehnt song description is rated positive
                cond1 = coher_indices & df.description_score_mvt_valence < mean_coher - threshold;
                cond2 = opp_indices & df.description_score_mvt_valence > mean_opp + threshold;
            else % in the case the coherehnt song description is rated negative
                cond1 = coher_indices & df.description_score_mvt_valence > mean_coher + threshold;
                cond2 = opp_indices & df.description_score_mvt_valence < mean_opp - threshold;
            end
            df(mvt_samples & (cond1 | cond2), :) = [];
            fprintf("removed %d rows from exp %d mvt %d\n",sum(mvt_samples & (cond1 | cond2)), exp_i, track_n);
        end
    end
elseif reduce == 3
    % df(df.description_valence_mean < 7 & ismember(df.track_condition, [1, 3]), :) = [];
    % df(df.description_valence_mean > 4 & ismember(df.track_condition, [2, 4]), :) = [];
    df(df.description_score_mvt_valence < 7 & ismember(df.track_condition, [1]), :) = [];
    df(df.description_score_mvt_valence > 4 & ismember(df.track_condition, [2]), :) = [];
    % df(df.description_score_mvt_valence_reference < 7, :) = [];
    % df(df.description_score_mvt_valence_reference_opp > 4, :) = [];
    threshold = 2;
    for exp_i = 1:8
        expid = "exp" + string(exp_i);
        for track_n = 1:4
            coher_indices = df.aggregated_condition_affective == "Aff Coher";
            opp_indices = df.aggregated_condition_affective == "Aff Opp";
            exp_samples = df.expid == expid;
            track_samples = df.track_number == track_n;
            mvt_samples = track_samples & exp_samples;

            mean_coher = mean(df(mvt_samples & coher_indices, "description_score_mvt_valence").Variables);
            mean_opp = mean(df(mvt_samples & opp_indices, "description_score_mvt_valence").Variables);
            if mean_coher > mean_opp % in the case the coherehnt song description is rated positive
                cond1 = coher_indices & df.description_score_mvt_valence < mean_coher - threshold;
                cond2 = opp_indices & df.description_score_mvt_valence > mean_opp + threshold;
            else % in the case the coherehnt song description is rated negative
                cond1 = coher_indices & df.description_score_mvt_valence > mean_coher + threshold;
                cond2 = opp_indices & df.description_score_mvt_valence < mean_opp - threshold;
            end
            df(mvt_samples & (cond1 | cond2), :) = [];
            fprintf("removed %d rows from exp %d mvt %d\n",sum(mvt_samples & (cond1 | cond2)), exp_i, track_n);
        end
    end
    
end

df.description_coher_score = mean([df.track_q3_1, df.track_q3_2], 2);

nr = height(df);
[~, tmpindx] = sort(df.goldsmi_gf_score);
df.groups_gf = ones(nr, 1);
df.groups_gf(tmpindx(floor(nr/3)+1 : floor(2*nr/3))) = 2;
df.groups_gf(tmpindx(floor(2*nr/3)+1 : end)) = 3;

tmpindx = abs(df.description_valence_trend_slope) < 0.5;
df.groups_vl_slope = ones(nr, 1);
df.groups_vl_slope(tmpindx) = 2;
df.groups_vl_slope(df.description_valence_trend_slope > 0.5) = 3;

tmpindx = abs(df.description_score_mvt_valence - 5) < 2;
df.groups_vl_mean = ones(nr, 1);
df.groups_vl_mean(tmpindx) = 2;
df.groups_vl_mean(df.description_score_mvt_valence - 5 > 2) = 3;
end
