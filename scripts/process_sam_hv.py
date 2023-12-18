#!/usr/bin/env python

# Import modules
import re
import argparse
import pandas as pd
import time
import datetime
import gzip
import bz2
import json

# Utility functions

def print_log(message):
    print("[", datetime.datetime.now(), "]\t", message, sep="")

def open_by_suffix(filename, mode="r"):
    if filename.endswith('.gz'):
        return gzip.open(filename, mode + 't')
    elif filename.endswith('.bz2'):
        return bz2.BZ2file(filename, mode)
    else:
        return open(filename, mode)

# Single-line functions

def get_next_alignment(sam_file):
    """Iterate through SAM file lines until gets an alignment line, then returns."""
    while True:
        l = next(sam_file, "EOF") # Get next line
        if not l: continue # Skip empty lines
        if l.startswith("@"): continue # Skip header lines
        return(l)

def check_flag(flag_sum, flag_dict, flag_name, flag_value):
    """Check if a flag sum includes a specific flag and return adjusted flag sum."""
    flag_sum = int(flag_sum)
    if flag_sum >= flag_value:
        flag_dict[flag_name] = True
        flag_sum -= flag_value
    else:
        flag_dict[flag_name] = False
    return flag_sum, flag_dict

def process_sam_flags(flag_sum):
    """Extract individual flags from flag sum."""
    flag_dict = {}
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "is_mate_2", 128)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "is_mate_1", 64)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "mate_aligned_reverse", 32)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "aligned_reverse", 16)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "no_paired_alignments", 8)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "no_single_alignments", 4)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "proper_paired_alignment", 2)
    flag_sum, flag_dict = check_flag(flag_sum, flag_dict, "in_pair", 1)
    return(flag_dict)

def extract_option(opt_list, query_value, default=None):
    """Extract specific optional field from list of optional fields."""
    fields = [f for f in opt_list if query_value in f]
    if len(fields) == 0: return(default)
    try:
        assert len(fields) == 1
    except AssertionError:
        print(query_value)
        print(fields)
        raise
    field = fields[0]
    pattern = "{}:.:(.*)".format(query_value)
    out_value = re.findall(pattern, field)[0]
    return(out_value)

def extract_optional_fields(opt_list, paired):
    """Extract relevant optional fields from Bowtie2 SAM alignment."""
    out = {}
    out["alignment_score"] = extract_option(opt_list, "AS")
    out["next_best_alignment"] = extract_option(opt_list, "XS")
    out["edit_distance"] = extract_option(opt_list, "NM")
    if paired:
        out["mate_alignment_score"] = extract_option(opt_list, "YS")
        out["pair_status"] = extract_option(opt_list, "YT")
    return(out)

def process_sam_alignment(sam_line, genomeid_taxid_map, paired):
    """Process a SAM alignment line."""
    fields_in = sam_line.strip().split("\t")
    out = {}
    out["query_name"] = fields_in[0]
    out.update(process_sam_flags(fields_in[1]))
    out["genome_id"] = fields_in[2]
    out["taxid"] = int(genomeid_taxid_map[fields_in[2]][0])
    # TODO: Get taxid from genome_id
    out["ref_start"] = int(fields_in[3]) - 1 # Convert from 1-indexing to 0-indexing
    out["map_qual"] = int(fields_in[4])
    out["cigar"] = fields_in[5]
    if paired:
        out["mate_genome_id"] = fields_in[6]
        out["mate_ref_start"] = int(fields_in[7]) - 1 # Convert as above
        out["fragment_length"] = abs(int(fields_in[8]))
    out["query_seq"] = fields_in[9]
    out["query_len"] = len(fields_in[9])
    out.update(extract_optional_fields(fields_in[10:], paired))
    return(out)

def process_sam_alignment_pair(fwd_line, rev_line, genomeid_taxid_map):
    """Process a pair of SAM alignment lines."""
    # Extract data from alignment entries
    fwd_dict = process_sam_alignment(fwd_line, genomeid_taxid_map, True)
    rev_dict = process_sam_alignment(rev_line, genomeid_taxid_map, True)
    # Verify concordant alignment
    try:
        assert fwd_dict["query_name"] == rev_dict["query_name"]
        assert fwd_dict["genome_id"] == rev_dict["genome_id"]
        assert fwd_dict["pair_status"] == rev_dict["pair_status"] == "CP"
        assert fwd_dict["fragment_length"] == rev_dict["fragment_length"]
        assert fwd_dict["ref_start"] == rev_dict["mate_ref_start"]
        assert rev_dict["ref_start"] == fwd_dict["mate_ref_start"]
        assert fwd_dict["in_pair"] == rev_dict["in_pair"] == True
        assert fwd_dict["proper_paired_alignment"] == rev_dict["proper_paired_alignment"] == True
    except AssertionError:
        print(fwd_line)
        print(rev_line)
        raise
    # Generate output line
    query_name = fwd_dict["query_name"]
    genome_id = fwd_dict["genome_id"]
    taxid = fwd_dict["taxid"]
    fragment_length = fwd_dict["fragment_length"]
    best_alignment_score_fwd = fwd_dict["alignment_score"]
    best_alignment_score_rev = rev_dict["alignment_score"]
    next_alignment_score_fwd = fwd_dict["next_best_alignment"]
    next_alignment_score_rev = rev_dict["next_best_alignment"]
    edit_distance_fwd = fwd_dict["edit_distance"]
    edit_distance_rev = rev_dict["edit_distance"]
    ref_start_fwd = fwd_dict["ref_start"]
    ref_start_rev = rev_dict["ref_start"]
    map_qual_fwd = fwd_dict["map_qual"]
    map_qual_rev = rev_dict["map_qual"]
    cigar_fwd = fwd_dict["cigar"]
    cigar_rev = rev_dict["cigar"]
    query_len_fwd = fwd_dict["query_len"]
    query_len_rev = rev_dict["query_len"]
    query_seq_fwd = fwd_dict["query_seq"]
    query_seq_rev = rev_dict["query_seq"]
    fields_out = [query_name, genome_id, taxid, fragment_length, best_alignment_score_fwd, best_alignment_score_rev, next_alignment_score_fwd, next_alignment_score_rev, edit_distance_fwd, edit_distance_rev, ref_start_fwd, ref_start_rev, map_qual_fwd, map_qual_rev, cigar_fwd, cigar_rev, query_len_fwd, query_len_rev, query_seq_fwd, query_seq_rev]
    return(fields_out)

def join_line(fields):
    "Convert a list of arguments into a TSV string for output."
    return("\t".join(map(str, fields)) + "\n")

# File-level functions

def process_paired_sam(sam_path, out_path, genomeid_taxid_map):
    """Process paired SAM file into a TSV."""
    with open_by_suffix(sam_path) as inf, open_by_suffix(out_path, "w") as outf:
        # Write headers
        headers = ["query_name", "genome_id", "taxid", "fragment_length", "best_alignment_score_fwd", "best_alignment_score_rev", "next_alignment_score_fwd", "next_alignment_score_rev", "edit_distance_fwd", "edit_distance_rev", "ref_start_fwd", "ref_start_rev", "map_qual_fwd", "map_qual_rev", "cigar_fwd", "cigar_rev", "query_len_fwd", "query_len_rev", "query_seq_fwd", "query_seq_rev"]
        header_line = join_line(headers)
        outf.write(header_line)
        # Write content
        end = False
        while True:
            # Get paired alignment entries (skipping headers and empty lines)
            fwd = get_next_alignment(inf)
            rev = get_next_alignment(inf)
            if fwd == "EOF":
                break
            elif rev == "EOF":
                raise ValueError("Unpaired SAM file.")
            # Process read pair
            fields = process_sam_alignment_pair(fwd, rev, genomeid_taxid_map)
            fields_joined = join_line(fields)
            outf.write(fields_joined)

# TODO: Process unpaired SAM

# Main function

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Process Bowtie2 SAM output into a TSV with additional information.")
    parser.add_argument("sam", help="Path to Bowtie2 SAM file.")
    parser.add_argument("genomeid_taxid_map", help="Path to JSON file containing genomeID/taxID mapping.")
    parser.add_argument("output_path", help="Output path for processed data frame.")
    parser.set_defaults(paired=True)
    parser.add_argument("-p", "--paired", dest="paired", action="store_true", help="Processed SAM file as containing paired read alignments (default: True).")
    parser.add_argument("-u", "--unpaired", dest="paired", action="store_false", help="Process SAM file as containing unpaired read alignments (default: False).")
    args = parser.parse_args()
    sam_path = args.sam
    out_path = args.output_path
    mapping_path = args.genomeid_taxid_map
    paired = args.paired
    # Start time tracking
    print_log("Starting process.")
    start_time = time.time()
    # Print parameters
    print_log("SAM file path: {}".format(sam_path))
    print_log("Mapping file path: {}".format(mapping_path))
    print_log("Output path: {}".format(out_path))
    print_log("Processing file as paired: {}".format(paired))
    # Import genomeID/taxID mapping
    print_log("Importing JSON mapping file...")
    with open_by_suffix(mapping_path) as inf:
        mapping = json.load(inf)
    print_log("JSON imported.")
    # Process SAM
    print_log("Processing SAM file...")
    if paired:
        process_paired_sam(sam_path, out_path, mapping)
    else:
        process_unpaired_sam(sam_path, out_path, mapping)
    print_log("File processed.")
    # Finish time tracking
    end_time = time.time()
    print_log("Total time elapsed: %.2f seconds" % (end_time - start_time))

if __name__ == "__main__":
    main()
