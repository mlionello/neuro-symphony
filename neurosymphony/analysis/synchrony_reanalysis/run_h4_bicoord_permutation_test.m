function run_h4_bicoord_permutation_test(datasetName, symphonies, nPerm)
% RUN_H4_BICOORD_PERMUTATION_TEST(datasetName, symphonies, nPerm)
%
% For each (expid, track_number) group, computes one Bi-Coordination
% Score per (button, event_type, draw) between the two groups: draw 0
% is the true labels, draws 1..nPerm are random re-partitions (same
% mechanics as run_h4_permutation_test.m).
%
% Requires MATLAB Statistics Toolbox (R2019a+) and Finn Upham's
% ActivityAnalysisToolbox_2.1-master/ (this repo).

if nargin < 1 || isempty(datasetName)
    datasetName = 'dataset.csv';
end
if nargin < 2
    symphonies = {'exp1', 'exp2'};
end
if nargin < 3 || isempty(nPerm)
    nPerm = 999;
end

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
datasetCsv  = fullfile(dataDir, datasetName);

if strcmp(datasetName, 'final_aggr.csv')
    suffix = '';
else
    suffix = '_truepos';
end
if ~isempty(symphonies)
    suffix = [suffix '_' strjoin(sort(symphonies), '-')];
end

outCsv = fullfile(repoRoot, 'analysis', 'figures', ...
                   ['h4_bicoord_permutation_test' suffix '.csv']);

FRAME_SIZE = 2;
MIN_PARTICIPANTS_PER_GROUP = 3;
BUTTON_LABELS = {'Power/Energy', 'Joy/Happiness', 'Sadness', ...
                  'Wonder/Surprise', 'Tension', 'Calm/Tranquillity'};
EVENT_TYPES = {'press_onset', 'release_onset', 'any_transition'};
BI_NBINS = 3;

addpath(toolboxPath);
rng(42);

%% ---- Load data ----
T = readtable(datasetCsv);
T.userid = cellstr(string(T.userid));
T.expid = cellstr(string(T.expid));
T.pressing_csv = cellstr(string(T.pressing_csv));
T.aggregated_condition_affective = cellstr(string(T.aggregated_condition_affective));

if ~isempty(symphonies)
    T = T(ismember(T.expid, symphonies), :);
end

fprintf('Dataset: %s (%d rows, symphonies: %s)\n', datasetCsv, height(T), strjoin(unique(T.expid), ', '));

%% ---- Pass 1: identify usable (expid, track_number) groups up front, for pre-allocation ----
[groupKeys, ~, groupIdx] = unique(T(:, {'expid', 'track_number'}), 'rows');
usableGroups = struct('expid', {}, 'trackNumber', {}, 'mats', {}, 'minLen', {}, 'coherIds', {}, 'oppIds', {});

for gi = 1:height(groupKeys)
    rows = T(groupIdx == gi, :);
    [mats, minLen, loadedIds] = load_track_group(rows, FRAME_SIZE, MIN_PARTICIPANTS_PER_GROUP);
    if isempty(loadedIds)
        continue
    end
    condAffByUser = containers.Map(rows.userid, rows.aggregated_condition_affective);
    coherIds = loadedIds(cellfun(@(u) strcmp(condAffByUser(u), 'Aff Coher'), loadedIds));
    oppIds = loadedIds(cellfun(@(u) strcmp(condAffByUser(u), 'Aff Opp'), loadedIds));
    if numel(coherIds) < MIN_PARTICIPANTS_PER_GROUP || numel(oppIds) < MIN_PARTICIPANTS_PER_GROUP
        continue
    end
    usableGroups(end+1) = struct('expid', groupKeys.expid{gi}, 'trackNumber', groupKeys.track_number(gi), ...
        'mats', mats, 'minLen', minLen, 'coherIds', {coherIds}, 'oppIds', {oppIds}); %#ok<AGROW>
end

nGroupsUsed = numel(usableGroups);
fprintf('Usable (expid, track_number) groups: %d\n', nGroupsUsed);

%% ---- Pre-allocate: (1 observed + nPerm null draws) x nGroupsUsed x nEventTypes x nButtons ----
nDraws = 1 + nPerm;
nRowsTotal = nDraws * nGroupsUsed * numel(EVENT_TYPES) * numel(BUTTON_LABELS);
results = cell(nRowsTotal, 8);
rowIdx = 0;

for gu = 1:nGroupsUsed
    expid = usableGroups(gu).expid;
    trackNumber = usableGroups(gu).trackNumber;
    mats = usableGroups(gu).mats;
    minLen = usableGroups(gu).minLen;
    coherIds = usableGroups(gu).coherIds;
    oppIds = usableGroups(gu).oppIds;
    nCoher = numel(coherIds);
    pool = [coherIds, oppIds];
    nPool = numel(pool);

    for drawIdx = 0:nPerm
        if drawIdx == 0
            pseudoCoher = coherIds;
            pseudoOpp = oppIds;
        else
            shuffled = pool(randperm(nPool));
            pseudoCoher = shuffled(1:nCoher);
            pseudoOpp = shuffled(nCoher+1:end);
        end

        for bIdx = 1:numel(BUTTON_LABELS)
            coherBinary = stack_button(mats, pseudoCoher, bIdx, minLen);
            oppBinary = stack_button(mats, pseudoOpp, bIdx, minLen);

            for eIdx = 1:numel(EVENT_TYPES)
                eventType = EVENT_TYPES{eIdx};

                coherFrames = build_event_frames(coherBinary, FRAME_SIZE, eventType);
                oppFrames = build_event_frames(oppBinary, FRAME_SIZE, eventType);

                AllCcoher = coherFrames';
                AllCopp = oppFrames';
                [~, pBi, ~, BinsBi] = relatedActivitiesTest(AllCcoher, AllCopp, BI_NBINS);
                [Cbi, feasBi, ~] = score_from_bins(pBi, BinsBi);

                rowIdx = rowIdx + 1;
                results(rowIdx, :) = {expid, trackNumber, BUTTON_LABELS{bIdx}, eventType, drawIdx, ...
                    Cbi, pBi, feasBi};
            end
        end
    end
end

results = results(1:rowIdx, :);
resultsTable = cell2table(results, 'VariableNames', ...
    {'expid', 'track_number', 'button', 'event_type', 'perm_idx', 'C', 'p', 'reliable'});
writetable(resultsTable, outCsv);
fprintf('nPerm=%d -> %d rows -> %s\n', nPerm, height(resultsTable), outCsv);

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
        error('run_h4_bicoord_permutation_test:build_event_frames:UnknownEventType', ...
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
