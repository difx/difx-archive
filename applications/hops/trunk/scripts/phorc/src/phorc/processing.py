import datetime
import optparse
import re
import string
import sys
import os
import math
import numpy as np
import shutil
import tempfile
from distutils.dir_util import copy_tree
from subprocess import Popen, PIPE


#hops package python libs
import mk4
import afio
import hopstest as ht

#local imports
from .baseline_fringe_product_list import baseline_fringe_product_list
from .fringe_file_handle import fringe_file_handle


def load_directory_fringe_files(dir_name, include_autos=False):
    #find all fringe files
    ff_list = ht.recursive_find_fringe_files(dir_name, include_autos)

    #load all fringes into memory
    fringe_objects = []
    for ff_name in ff_list:
        f_obj = fringe_file_handle()
        f_obj.load(ff_name)
        if(f_obj.is_valid):
            fringe_objects.append(f_obj)

    return fringe_objects

def filter_fringe_files_on_discrete_quantity(fringe_object_list, quantity_name, quantity_value_list):
    #returns a list of fringe file object, the list is composed of fringe file objects
    #which for the given the name of a quanity, have values which match in the value list
    #this is not particularly efficient
    #for example if we wanted to get a list of all fringe files associated with the 'GE' baseline
    #then we would call
    #single_baseline_list = filter_fringe_files_on_discrete_quantity(obj_list, quantity_name="baseline", ["GE"] )
    #or if we wanted to filer on files processed with the same control file (only works with name at the moment)
    #we could call cf_list = filter_fringe_files_on_discrete_quantity(obj_list, quantity_name="control_filename", ["./cf_GHEVY_ff"])

    ret_list = []
    for x in fringe_object_list:
        #TODO make robust agains missing values/incorrect value names
        val = getattr(x, quantity_name)
        for y in quantity_value_list:
            if val == y:
                ret_list.append(x)
                break
    return ret_list

def filter_fringe_files_on_value_range(fringe_object_list, quantity_name, low_value, high_value):
    #returns a list of fringe file objects, the list is composed of fringe file objects
    #which have the named quantity value in the given range
    low = low_value
    high = high_value
    if high < low:
        high = low_value
        low = high_value

    ret_list = []
    for x in fringe_object_list:
        #TODO make robust against missing values/incorrect value names
        val = getattr(x, quantity_name)
        if val < high and low < val:
                ret_list.append(x)

    return ret_list

def join_fringes_into_baseline_collection(fringe_object_list, station_list, include_autos=False, only_complete=True):
    #this function takes individual fringe files (for each scan, baseline, and polarization product)
    #and assembles the polarization product files together by baseline for each scan
    #TODO, make this more robust against files generated by control files with same name, but different contents

    #form the list of baselines
    baselines = []
    for a in station_list:
        for b in station_list:
            if include_autos == True or a != b:
                baselines.append(a+b)

    bline_collection_list = []
    for obj in fringe_object_list:
        if obj.baseline in baselines:
            sflist = baseline_fringe_product_list()
            sflist.root_id = obj.root_id
            sflist.baseline = obj.baseline
            sflist.scan_name = obj.scan_name
            sflist.control_filename = obj.control_filename
            is_present = False
            for sfl in bline_collection_list:
                if sfl == sflist:
                    sfl.add_fringe_object(obj)
                    is_present = True
                    break
            if is_present is False:
                sflist.add_fringe_object(obj)
                bline_collection_list.append(sflist)

    ret_list = []
    if only_complete is True:
        #strip out incomplete baselines
        #we need to make sure that each candidate baseline has all pol products
        for x in bline_collection_list:
            if x.is_complete() is True:
                ret_list.append(x)
        return ret_list
    else:
        return bline_collection_list

def filter_baseline_collections_on_control(baseline_collection_list, control_filename):
    #selects all baseline fringe collections based on common control file
    collection_list = []
    for obj in baseline_collection_list:
        if obj.control_filename == control_filename:
            collection_list.append(obj)
    return collection_list
    

def collect_baseline_collection_composite_values(obj_list, value_name):
    #collect a value from the baseline collections 
    #must ensure that the values are initialized and we have a complete collection
    value_list = []
    for obj in obj_list:
        if obj.is_complete() is True:
            obj.init_values()
            add_value_to_list(value_list, getattr(obj, value_name) )
    return value_list


def collect_baseline_collection_values(scan_list, value_name, pol_list=["XX", "XY", "YY", "YX"]):
    #scan list is a list of baseline_fringe_product_list objects
    value_list = []
    for scan in scan_list:
        if scan.xx_obj != None and "XX" in pol_list:
            add_value_to_list(value_list, getattr(scan.xx_obj, value_name) )
        if scan.xy_obj != None and "XY" in pol_list:
            add_value_to_list(value_list, getattr(scan.xy_obj, value_name) )
        if scan.yy_obj != None and "YY" in pol_list:
            add_value_to_list(value_list, getattr(scan.yy_obj, value_name) )
        if scan.yx_obj != None and "YX" in pol_list:
            add_value_to_list(value_list, getattr(scan.yx_obj, value_name) )
    return value_list

def collect_baseline_collection_value_pairs(scan_list, value_name1, value_name2, pol_list=["XX", "XY", "YY", "YX"]):
    #scan list is a list of baseline_fringe_product_list objects
    value_list1 = []
    value_list2 = []
    for scan in scan_list:
        if scan.xx_obj != None and "XX" in pol_list:
            add_value_to_list(value_list1, getattr(scan.xx_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.xx_obj, value_name2) )
        if scan.xy_obj != None and "XY" in pol_list:
            add_value_to_list(value_list1, getattr(scan.xy_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.xy_obj, value_name2) )
        if scan.yy_obj != None and "YY" in pol_list:
            add_value_to_list(value_list1, getattr(scan.yy_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.yy_obj, value_name2) )
        if scan.yx_obj != None and "YX" in pol_list:
            add_value_to_list(value_list1, getattr(scan.yx_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.yx_obj, value_name2) )
    if len(value_list1) != len(value_name2): #error, inequal number of values, return nothing
        value_list1 = []
        value_list2 = []
        print "Error, collect_value_pairs: mis-matched value list lengths"
    return [value_list1, value_list2]

def collect_baseline_collection_value_triplets(scan_list, value_name1, value_name2, value_name3, pol_list=["XX", "XY", "YY", "YX"]):
    #scan list is a list of baseline_fringe_product_list objects
    value_list1 = []
    value_list2 = []
    value_list3 = []
    for scan in scan_list:
        if scan.xx_obj != None and "XX" in pol_list:
            add_value_to_list(value_list1, getattr(scan.xx_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.xx_obj, value_name2) )
            add_value_to_list(value_list3, getattr(scan.xx_obj, value_name3) )
        if scan.xy_obj != None and "XY" in pol_list:
            add_value_to_list(value_list1, getattr(scan.xy_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.xy_obj, value_name2) )
            add_value_to_list(value_list3, getattr(scan.xy_obj, value_name3) )
        if scan.yy_obj != None and "YY" in pol_list:
            add_value_to_list(value_list1, getattr(scan.yy_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.yy_obj, value_name2) )
            add_value_to_list(value_list3, getattr(scan.yy_obj, value_name3) )
        if scan.yx_obj != None and "YX" in pol_list:
            add_value_to_list(value_list1, getattr(scan.yx_obj, value_name1) )
            add_value_to_list(value_list2, getattr(scan.yx_obj, value_name2) )
            add_value_to_list(value_list3, getattr(scan.yx_obj, value_name3) )
    if len(value_list1) != len(value_name2) or len(value_list1) != len(value_name3): #error, inequal number of values, return nothing
        value_list1 = []
        value_list2 = []
        value_list3 = []
        print "Error, collect_value_triplets: mis-matched value list lengths"
    return [value_list1, value_list2, value_list3]
    
    
def sort_collections_by_baseline(baseline_collection_list):
    #returns a list of lists, each (sub)list contains collections corresponding
    #to a single baseline, brute force
    bline_set = set()
    for x in baseline_collection_list:
        bl = x.baseline
        bline_set.add(bl)
        
    n_blines = len(bline_set)
    sorted_list = [ [] for n in xrange(n_blines) ]
    
    for x in baseline_collection_list:
        count = 0
        for y in bline_set:
            if x.baseline == y:
                sorted_list[count].append(x)
            count += 1
    
    return sorted_list

def sort_objects_by_quantity(object_list, quantity_name, reverse_boolean=False):
    #sorts low to high (if reverse is True, then high to low)
    object_list.sort(key=lambda x: getattr(x,quantity_name), reverse=reverse_boolean)
    
def add_value_to_list(val_list, val_obj):
    if isinstance(val_obj, (float, int, long) ):
        val_list.append(val_obj)
        
def collect_object_values(obj_list, value_name):
    #collect a value from a list of objects
    value_list = []
    for obj in obj_list:
            add_value_to_list(value_list, getattr(obj, value_name) )
    return value_list

def collect_object_value_pairs(obj_list, value_name1, value_name2, sort_items=False):
    #collect set of value pairs from a list of objects 
    #(if sort_items=True, we sort them on the first value)
    value_list1 = []
    value_list2 = []
    ret_value_list1 = []
    ret_value_list2 = []
    
    for obj in obj_list:
            add_value_to_list(value_list1, getattr(obj, value_name1) )
            add_value_to_list(value_list2, getattr(obj, value_name2) )
            
    if sort_items is True:
        zipped_items = zip(value_list1, value_list2)
        zipped_items.sort()
        ret_value_list1 = [x for (x,y) in zipped_items]
        ret_value_list2 = [y for (x,y) in zipped_items]
    else:
        ret_value_list1 = value_list1
        ret_value_list2 = value_list2
    
    return [ret_value_list1, ret_value_list2]


def locate_pcphase_candidate_scans(fringe_object_list, reference_station, remote_station_list, snr_limits=[100, 250], dtec_tol=0.1):
    #function to locate scans which can serve as
    snr_low = min(snr_limits)
    snr_high = max(snr_limits)

    #first pass, get fringe files which satisfy the snr constraints
    #on the baselines of interest and index them
    scan_index = []
    for obj in fringe_object_list:
        # print "root id = ", obj.root_id, "baseline = ", obj.baseline, " pol = ", obj.pol_product
        #check it is a baseline we are interested in
        ref_present = False
        rem_present = False
        if reference_station in obj.baseline:
            ref_present = True
        for st in remote_station_list:
            if st in obj.baseline:
                rem_present = True

        if rem_present and ref_present:
            snr = obj.snr
            if snr < snr_high and snr > snr_low:
                sflist = baseline_fringe_product_list()
                sflist.root_id = obj.root_id
                sflist.baseline = obj.baseline
                sflist.scan_name = obj.scan_name
                sflist.control_filename = obj.control_filename
                is_present = False
                for sfl in scan_index:
                    if sfl == sflist:
                        sfl.add_fringe_object(obj)
                        is_present = True
                        break
                if is_present is False:
                    sflist.add_fringe_object(obj)
                    scan_index.append(sflist)

    #strip out incomplete baselines
    #we need to make sure that each candidate baseline has all pol products
    prelim_candidate_list = []
    for x in scan_index:
        if x.is_complete() is True:
            prelim_candidate_list.append(x)

    #now for each candidate, make sure that maximum deviation from
    #the mean in the dTEC solutions
    #for all polarization products is within tolerance
    candidate_list = []
    for x in prelim_candidate_list:
        if x.get_dtec_max_deviation() <= dtec_tol:
            candidate_list.append(x)

    for x in candidate_list:
        print str(x.root_id) + " - " + str(x.baseline) + " - " + str(x.get_dtec_max_deviation() ) +  " - dtec list = " + str(x.get_dtec_list())

    #now return the index of complete baselines
    return candidate_list

def launch_processes_in_parallel(full_arg_list, max_num_processes=1):
    #launch processes in parallel
    threads = []
    generated_fringe_files = []
    processed_args_list = []
    arg_list = full_arg_list
    #generate new threads, and monitor until all data is processed
    while threads or arg_list:

        #spawn a new thread if we are not using the max number of processes and there are still files to process
        if (len(threads) < max_num_processes) and (len(arg_list) != 0 ):
            t_args = arg_list.pop()
            t = ht.FourFitThread(target=ht.fourfit_generate_fringe, args=t_args)
            t.setDaemon(True)
            t.start()
            threads.append(t)

        #we have already spawned the max number of process (or there is no data left to run on) so just
        #monitor the running processes and remove them once they are finished
        else:
            for thread in threads:
                if not thread.isAlive():
                    generated_files = thread.get_return_value()
                    processed_args= thread.get_input_args()
                    #generated_files = thread.join()
                    generated_fringe_files.extend( generated_files )
                    for n in range(0, len(generated_files) ):
                        processed_args_list.append( processed_args )
                    threads.remove(thread)
                    
    return generated_fringe_files, processed_args_list

def temporary_fringe_single_scan(root_filename, control_file, fourfit_options, set_string=""):
    #first figure out the root directory, scan and the experiment number
    abs_root_path = os.path.abspath(root_filename)
    scan_dir = os.path.dirname(abs_root_path)
    exp_dir = os.path.dirname(scan_dir)
    root_filename = os.path.split(abs_root_path)[1]
    scan_name = os.path.split(scan_dir)[1]
    exp_name = os.path.split(exp_dir)[1]

    control_file_path = os.path.abspath(control_file)

    #copy the root directories contents over to a temp directory mirroring
    #the file tree of the original scan
    temp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(temp_dir, exp_name, scan_name)
    copy_tree(scan_dir, tmp_path)
    #set root to point to the new temp directory
    root_file_path = os.path.join(tmp_path, root_filename)
    
    options = fourfit_options
    baseline = ""
    
    fringe_file_list = ht.fourfit_generate_fringe(options, baseline, control_file_path, root_file_path, set_commands=set_string)
    
    #return the path to the temp directory and fringe files for later use and deletion
    return [tmp_path, fringe_file_list]

#brute force way to determine the hash of a control file and set string
def get_control_hash(root_filename, control_file, set_string):

    #quick fourfit test just to get the hash of the control file for later id
    ff_opts = " -P XX "
    [tmp_dir, tmp_fringe_list] = temporary_fringe_single_scan(root_filename, control_file, ff_opts, set_string)

    if( len(tmp_fringe_list) < 1):
        print "Test fringe failed."
        sys.exit()

    #get the control file hash id we need for fringe file sorting later
    tmp_fringe_handle = fringe_file_handle()
    tmp_fringe_handle.load(tmp_fringe_list[0])
    control_hash = tmp_fringe_handle.control_file_hash
    set_string_hash = tmp_fringe_handle.set_string_hash

    #clean up temp dir
    shutil.rmtree(tmp_dir, ignore_errors=False, onerror=None)
    
    return [control_hash, set_string_hash]
    
################################################################################
def compute_2d_pareto_front(obj_list, par1, par2, maximize1=True, maximize2=True):
    #returns a list of objects on the pareto front of par1 and par2 
    #if maximize1 or maximize2 is false, then the objective for that variable will
    #be minimization rather than maximization
    
    #empty set of pareto points
    pareto_set = set()
    
    #sort the list along the 1st axis
    sort_objects_by_quantity(obj_list, par1, maximize1)

    #take the first object and add it to the pareto set
    pareto_set.add(obj_list[0])
    
    #slow O(N^2) search using simple cull method
    if maximize1 is True and maximize2 is True:
        for n in range(1, len(obj_list)):
            x = obj_list[n]
            on_interior = False
            p1x = getattr(x,par1)
            p2x = getattr(x,par2) 
            for y in pareto_set:
                #now determine if x is on the interior
                p1y = getattr(y,par1)
                p2y = getattr(y,par2)
                if p1x <= p1y and p2x <= p2y:
                    on_interior = True
                    break
            if on_interior is False:
                #now prune any points in the pareto front which
                #are interior to this new point
                for y in pareto_set:
                    p1y = getattr(y,par1)
                    p2y = getattr(y,par2)
                    if p1y <= p1x and p2y <= p2x:
                        pareto_set.remove(y)
                #add the new point to the pareto front
                pareto_set.add(x)
    elif maximize1 is True and maximize2 is False:
        for n in range(1, len(obj_list)):
            x = obj_list[n]
            on_interior = False
            p1x = getattr(x,par1)
            p2x = getattr(x,par2) 
            for y in pareto_set:
                #now determine if x is on the interior
                p1y = getattr(y,par1)
                p2y = getattr(y,par2)
                if p1x <= p1y and p2x >= p2y:
                    on_interior = True 
                    break
            if on_interior is False:
                #now prune any points in the pareto front which
                #are interior to this new point
                for y in pareto_set:
                    p1y = getattr(y,par1)
                    p2y = getattr(y,par2)
                    if p1y <= p1x and p2y >= p2x:
                        pareto_set.remove(y)
                #add the new point to the pareto front
                pareto_set.add(x)
    elif maximize1 is False and maximize2 is True:
        for n in range(1, len(obj_list)):
            x = obj_list[n]
            on_interior = False
            p1x = getattr(x,par1)
            p2x = getattr(x,par2) 
            for y in pareto_set:
                #now determine if x is on the interior
                p1y = getattr(y,par1)
                p2y = getattr(y,par2)
                if p1x >= p1y and p2x <= p2y:
                    on_interior = True
                    break
            if on_interior is False:
                #now prune any points in the pareto front which
                #are interior to this new point
                for y in pareto_set:
                    p1y = getattr(y,par1)
                    p2y = getattr(y,par2)
                    if p1y >= p1x and p2y <= p2x:
                        pareto_set.remove(y)
                #add the new point to the pareto front
                pareto_set.add(x)
    elif maximize1 is False and maximize2 is False:
        for n in range(1, len(obj_list)):
            x = obj_list[n]
            on_interior = False
            p1x = getattr(x,par1)
            p2x = getattr(x,par2) 
            for y in pareto_set:
                #now determine if x is on the interior
                p1y = getattr(y,par1)
                p2y = getattr(y,par2)
                if p1x >= p1y and p2x >= p2y:
                    on_interior = True
                    break
            if on_interior is False:
                #now prune any points in the pareto front which
                #are interior to this new point
                for y in pareto_set:
                    p1y = getattr(y,par1)
                    p2y = getattr(y,par2)
                    if p1y >= p1x and p2y >= p2x:
                        pareto_set.remove(y)
                #add the new point to the pareto front
                pareto_set.add(x)
    
    pareto_list = []
    for y in pareto_set:
        pareto_list.append(y)
    
    return pareto_list

################################################################################
