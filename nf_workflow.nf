#!/usr/bin/env nextflow
nextflow.enable.dsl=2

params.input_type = "public_library"  // Input type, either [public_library, mgf_file]

params.input_library = "ALL_GNPS_NO_PROPOGATED" // Which GNPS library to use as a query (e.g., "GNPS-LIBRARY" or "ALL_GNPS_NO_PROPOGATED")
params.input_mgf = "mgf_file.mgf" // Pickle file to use as a query

// Search Parameters
// Which index to search against, usually [massivedata_index, gnpslibrary], massivekb_index for proteomics
params.search_index = "massivedata_index" 
params.analog_search = false // Whether to perform analog search
params.no_cache = false // Whether to use the cache
params.lower_delta = 130 
params.upper_delta = 200 
params.pm_tolerance = 0.05 // PM tolerance for analog search
params.fragment_tolerance = 0.05 // Fragment tolerance for analog search
params.cosine_threshold = 0.7 // Cosine threshold for analog search

TOOL_FOLDER = "$baseDir/bin"

// Download query libraries from GNPS in MGF format
process collectFromGNPS {
    conda "$TOOL_FOLDER/conda_env.yml"

    output:
    path 'gnps_library.mgf', emit: collected_mgf

    """
    wget http://external.gnps2.org/gnpslibrary/${params.input_library}.mgf -O gnps_library.mgf
    """
}

// Search against the index provided an MGF file using GNPS2 API
process searchMGF {
    publishDir "nf_output", mode: 'copy'

    conda "$TOOL_FOLDER/conda_env.yml"
    
    input:
    path input_mgf

    output:
    path 'results.csv'

    """
    python $TOOL_FOLDER/search_mgf_against_index.py --input_mgf ${input_mgf} \
                                                    --search_index ${params.search_index} \
                                                    --output results.csv \
                                                    --analog ${params.analog_search} \
                                                    --no_cache ${params.no_cache} \
                                                    --lower_delta ${params.lower_delta} \
                                                    --upper_delta ${params.upper_delta} \
                                                    --pm_tolerance ${params.pm_tolerance} \
                                                    --fragment_tolerance ${params.fragment_tolerance} \
                                                    --cosine_threshold ${params.cosine_threshold}
    """
}

workflow {

    if (params.input_type == "public_library") {
        data = collectFromGNPS()
    } else if (params.input_type == "mgf_file") {
        data = Channel.fromPath(params.input_mgf)
    } else {
        throw new RuntimeException("Unknown input type")
    }

    searchMGF(data)
}