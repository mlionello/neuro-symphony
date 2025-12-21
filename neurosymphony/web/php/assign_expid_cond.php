<?php

function get_experiment_id($completed_exp, $log_file, $reset_time) {
    $framework = json_decode(file_get_contents($_SESSION['overall_consts']), true);

    $bad_participants = ['2126c473d9a19d36', '2fc878cc99fe485c', '308995cbcefd08d6',
     '4030f86f4e14b2fe', '693d83d8c1ed9574', '7ca2a2c9f745bede', '723505417f6af41d',
     '970f2a6ffced5bf6', 'af5b81e7e3c8ab89', 'c5ebc1db0f7b4aef', 'd0cfcee74af0c73d',
     'f86130e86879eddd', 'fce234917a1a7e98'];

    // Read the CSV file into an array
    $experiment_log = [];
    if (($handle = fopen($log_file, "r")) !== FALSE) {

        while (($row = fgetcsv($handle, 0, ',', '"', '\\')) !== FALSE) {
            list($user_id, $timestamp, $exp_started_id, $exp_finished_id, $category) = $row;

            // Skip this row if the user_id is in $bad_participants
            if (in_array($user_id, $bad_participants)) {
                error_log($user_id);
                continue;
            }

            $exp_id = !empty($exp_started_id) ? $exp_started_id : $exp_finished_id;

            if (!isset($experiment_log[$exp_id])) {
                $experiment_log[$exp_id] = [
                    'started_timestamp' => [],
                    'indx_category_at_start' => [],
                    'completed_timestamp' => [],
                    'indx_category_at_completion' => []
                ];
            }

            if (!empty($exp_started_id)) {
                $experiment_log[$exp_id]['started_timestamp'][] = (int) $timestamp;
                $experiment_log[$exp_id]['indx_category_at_start'][] = (int) $category;
            }
            if (!empty($exp_finished_id)) {
                $experiment_log[$exp_id]['completed_timestamp'][] = (int) $timestamp;
                $experiment_log[$exp_id]['indx_category_at_completion'][] = (int) $category;
            }
        }
        fclose($handle);
    }

    // Load the total number of lines in shuffled_combinations.csv
    // this can be evaluated for each file inside the loop
    $total_nb_conditions = 24; //count(file($_SESSION['exp_conditions'], FILE_SKIP_EMPTY_LINES));

    date_default_timezone_set('UTC');
    $current_time = time();
    $one_hour_ago = $current_time - $reset_time;

    $cond_counter_per_exp = []; // To track the ratio of assigned conditions for each experiment

    $remaining_experiments = array_diff($framework['exp_id'], $completed_exp);
    // Loop through the ordered list of experiment IDs
    foreach ($remaining_experiments as $exp_id) {
        $started_timestamps = isset($experiment_log[$exp_id]['started_timestamp']) && is_array($experiment_log[$exp_id]['started_timestamp'])
            ? $experiment_log[$exp_id]['started_timestamp']
            : [];

        // Filter timestamps within the last hour
        $started_last_hour_indices = array_keys(array_filter($started_timestamps, function($timestamp) use ($one_hour_ago) {
            return $timestamp >= $one_hour_ago;
        }));

        // Get array of indices of started_last_hour
        $started_condition = isset($experiment_log[$exp_id]['indx_category_at_start']) && is_array($experiment_log[$exp_id]['indx_category_at_start'])
            ? $experiment_log[$exp_id]['indx_category_at_start']
            : [];
        $indices_for_started_sessions = array_intersect_key($started_condition, array_flip($started_last_hour_indices));

        // Get indices for completed sessions
        $indices_for_completed_sessions = isset($experiment_log[$exp_id]['indx_category_at_completion']) && is_array($experiment_log[$exp_id]['indx_category_at_completion'])
            ? $experiment_log[$exp_id]['indx_category_at_completion']
            : [];

        // Concatenate indices
        $all_conditions = array_merge($indices_for_started_sessions, $indices_for_completed_sessions);

        // Get unique indices of the conditions assigned
        $unique_conditions_assigned = array_unique($all_conditions);

        // Check if all conditions are not used, if so return this experiment
        if (count($unique_conditions_assigned) < $total_nb_conditions) {
            // Find the lowest condition index that has not been assigned
            $all_possible_conditions = range(0, $total_nb_conditions - 1);
            $unassigned_conditions = array_diff($all_possible_conditions, $unique_conditions_assigned);
            sort($unassigned_conditions);
            return [$exp_id, $unassigned_conditions[0]]; // Return the experiment ID and first unassigned condition
        }

        $cond_counter_per_exp[] = count($unique_conditions_assigned) / $total_nb_conditions; // Keep as float ratio

        // Count occurrences of each condition for this experiment
        $all_indices_counts = array_count_values($all_conditions);

        // Calculate the total usage for each condition
        $usage_count_per_condition = [];
        for ($i = 0; $i < $total_nb_conditions; $i++) {
            $count = isset($all_indices_counts[$i]) ? $all_indices_counts[$i] : 0;
            $usage_count_per_condition[$i] = $count;
        }

        // Find the condition with the lowest occurrence
        $min_usage_count = min($usage_count_per_condition);
        $conditions_with_min_usage = array_keys($usage_count_per_condition, $min_usage_count);
        sort($conditions_with_min_usage); // Sort to ensure we pick the smallest index if there is a tie
        $condition_with_lowest_occurrence_per_exp[] = $conditions_with_min_usage[0];
    }

    // If all conditions for all experiments are filled, return the exp with the lowest ratio
    $min_ratio_index = array_keys($cond_counter_per_exp, min($cond_counter_per_exp))[0];
    return [$framework['exp_id'][$min_ratio_index], $condition_with_lowest_occurrence_per_exp[$min_ratio_index]];
}

?>
