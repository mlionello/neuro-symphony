function run_h4_pca_composite_table()
% RUN_H4_PCA_COMPOSITE_TABLE()
%
% "all 6 buttons" branch of the within-synchrony table: scores the
% composite "PC1" signal built by pca_composite_events.py (1st principal
% component across the 6 buttons' held-state series, pooled per
% movement, binarized by sign).
%
% Writes: analysis/figures/h4_pca_composite_toolbox_exp1-exp2.csv, same
% schema as h4_within_aff_condition_toolbox_exp1-exp2.csv.
%
% Requires MATLAB Statistics Toolbox (R2019a+) and Finn Upham's
% ActivityAnalysisToolbox_2.1-master/.

scriptPath  = mfilename('fullpath');
repoRoot    = fileparts(fileparts(fileparts(scriptPath)));
if exist(fullfile(repoRoot, 'preprocessing', 'dataset.csv'), 'file')
    dataDir = fullfile(repoRoot, 'preprocessing');
else
    dataDir = repoRoot;
end
toolboxPath = fullfile(repoRoot, 'ActivityAnalysisToolbox_2.1-master');
if ~isfolder(toolboxPath)
    error('Finn Upham''s ActivityAnalysisToolbox 2.1 not found: %s', toolboxPath);
end
cd(dataDir);
datasetCsv  = fullfile(repoRoot, 'analysis', 'figures', 'pca_composite_manifest_exp1-exp2.csv');
outCsv      = fullfile(repoRoot, 'analysis', 'figures', 'h4_pca_composite_toolbox_exp1-exp2.csv');

FRAME_SIZE = 2;
MIN_PARTICIPANTS_PER_GROUP = 3;
BUTTON_LABELS = {'PC1_composite'};
EVENT_TYPES = {'press_onset'};
WITHIN_NBINS = 5;
CONDITIONS = {'Aff Coher', 'Aff Opp'};

addpath(toolboxPath);

%% ---- Load data ----
T = readtable(datasetCsv);
T.userid = cellstr(string(T.userid));
T.expid = cellstr(string(T.expid));
T.pressing_csv = cellstr(string(T.pressing_csv));
T.aggregated_condition_affective = cellstr(string(T.aggregated_condition_affective));

fprintf('Dataset: %s (%d rows, symphonies: %s)\n', datasetCsv, height(T), strjoin(unique(T.expid), ', '));

%% ---- Iterate (expid, track_number) groups ----
[groupKeys, ~, groupIdx] = unique(T(:, {'expid', 'track_number'}), 'rows');
results = cell(0, 9);
nGroupsUsed = 0;

for gi = 1:height(groupKeys)
    expid = groupKeys.expid{gi};
    trackNumber = groupKeys.track_number(gi);
    rows = T(groupIdx == gi, :);

    [mats, minLen, loadedIds] = load_track_group(rows, FRAME_SIZE, MIN_PARTICIPANTS_PER_GROUP);
    if isempty(loadedIds)
        continue
    end

    condAffByUser = containers.Map(rows.userid, rows.aggregated_condition_affective);
    usedThisGroup = false;

    for cIdx = 1:numel(CONDITIONS)
        condLabel = CONDITIONS{cIdx};
        groupIds = loadedIds(cellfun(@(u) strcmp(condAffByUser(u), condLabel), loadedIds));

        if numel(groupIds) < MIN_PARTICIPANTS_PER_GROUP
            continue
        end
        usedThisGroup = true;

        for bIdx = 1:numel(BUTTON_LABELS)
            groupBinary = stack_button(mats, groupIds, bIdx, minLen);

            for eIdx = 1:numel(EVENT_TYPES)
                eventType = EVENT_TYPES{eIdx};

                frames = build_event_frames(groupBinary, FRAME_SIZE, eventType);  % nGroup x nFrames

                ACgroup = mean(frames, 1)';
                [~, pVal, ~, bins] = simpleActivityTest(ACgroup, numel(groupIds), WITHIN_NBINS);
                [Cval, feasible, nBins] = score_from_bins(pVal, bins);

                results(end+1, :) = {expid, trackNumber, BUTTON_LABELS{bIdx}, eventType, condLabel, ...
                    Cval, pVal, feasible, feasible && nBins == 2}; %#ok<AGROW>
            end
        end
    end

    if usedThisGroup
        nGroupsUsed = nGroupsUsed + 1;
    end
end

resultsTable = cell2table(results, 'VariableNames', ...
    {'expid', 'track_number', 'button', 'event_type', 'condition', 'C', 'p', 'feasible', 'degenerate_2bin'});
writetable(resultsTable, outCsv);
nDegenerate = sum(resultsTable.degenerate_2bin);
fprintf('Used %d (expid, track_number) groups -> %d rows -> %s\n', nGroupsUsed, height(resultsTable), outCsv);
if nDegenerate > 0
    fprintf(['%d rows flagged degenerate_2bin=true (within-collection test fell back to 2 bins, ' ...
        'toolbox dof=0 pins p at exactly 0 -- excluded from downstream aggregation).\n'], nDegenerate);
end

end

%% ==================== Local functions ====================

function [mats, minLen, loadedIds] = load_track_group(rows, frameSize, minParticipants)
mats = containers.Map('KeyType', 'char', 'ValueType', 'any');
for i = 1:height(rows)
    p = rows.pressing_csv{i};
    uid = rows.userid{i};
    if isempty(p) || ~isfile(p)
        continue
    end
    raw = readmatrix(p);
    if size(raw, 2) < 2
        continue
    end
    buttons = double(raw(:, 2:end) ~= 0);
    mats(uid) = buttons;
end

if mats.Count < 2 * minParticipants
    mats = containers.Map('KeyType', 'char', 'ValueType', 'any');
    minLen = 0; loadedIds = {};
    return
end

loadedIds = keys(mats);
lens = cellfun(@(k) size(mats(k), 1), loadedIds);
minLen = min(lens);
if minLen < frameSize * 10
    mats = containers.Map('KeyType', 'char', 'ValueType', 'any');
    minLen = 0; loadedIds = {};
    return
end

for i = 1:numel(loadedIds)
    k = loadedIds{i};
    v = mats(k);
    mats(k) = v(1:minLen, :);
end
end

function binary = stack_button(mats, ids, buttonIdx, minLen)
n = numel(ids);
binary = zeros(n, minLen);
for i = 1:n
    v = mats(ids{i});
    binary(i, :) = v(1:minLen, buttonIdx)';
end
end

function frames = build_event_frames(binaryMatrix, frameSize, eventType)
switch eventType
    case 'held_state'
        stream = binaryMatrix;
    case 'press_onset'
        prev = [zeros(size(binaryMatrix, 1), 1), binaryMatrix(:, 1:end-1)];
        stream = double(binaryMatrix == 1 & prev == 0);
    case 'release_onset'
        prev = [zeros(size(binaryMatrix, 1), 1), binaryMatrix(:, 1:end-1)];
        stream = double(binaryMatrix == 0 & prev == 1);
    case 'any_transition'
        prev = [zeros(size(binaryMatrix, 1), 1), binaryMatrix(:, 1:end-1)];
        stream = double(binaryMatrix ~= prev);
    otherwise
        error('run_h4_pca_composite_table:build_event_frames:UnknownEventType', ...
            'Unknown event type %s', eventType);
end
frames = frame_activity_from_binary(stream, frameSize);
end

function frames = frame_activity_from_binary(binaryMatrix, frameSize)
[nP, nS] = size(binaryMatrix);
nF = floor(nS / frameSize);
trimmed = binaryMatrix(:, 1:nF*frameSize);
frames = zeros(nP, nF);
for i = 1:nP
    chunk = reshape(trimmed(i, :), frameSize, nF);
    frames(i, :) = max(chunk, [], 1) > 0;
end
end

function [C, feasible, nBins] = score_from_bins(pVal, bins)
feasible = ~isempty(bins);
if feasible
    nBins = size(bins, 1);
    C = min(-log10(max(pVal, 1e-16)), 16.0);
else
    nBins = 0;
    C = NaN;
end
end
