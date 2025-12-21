<?php

function loadCSV($filename, $indices = null) {
    $rows = array_map( function($v){return str_getcsv($v, ",", "\"", "\\");}, file($filename));
    $header = array_shift($rows);
    $csv = [];

    foreach ($rows as $index => $row) {
        if (count($header) !== count($row)) {
            // Include the row with missing elements as null
            $row = array_pad($row, count($header), null);
        }
        $data = array_combine($header, $row);
        if (is_array($indices) && !in_array($index, $indices)) {
            continue;
        }
        $csv[] = $data;
    }

    return $csv;
}

?>
