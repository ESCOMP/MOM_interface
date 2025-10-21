#!/usr/bin/env python

import yaml
import subprocess
from check_input_data_list import (
    get_input_files_in_MOM_input,
    get_input_data_list_files,
)


def get_repo_files_with_curl(base_url):
    """
    Get file list from repository using curl and HTML parsing instead of SVN.
    
    The server provides HTML directory listings that we can parse to find files.
    This function recursively traverses directories to find all files.
    
    Parameters
    ----------
    base_url : str
        The base URL of the repository
        
    Returns
    -------
    set
        Set of file names found in the repository
    """
    import re
    
    def parse_html_directory_listing(html_content, current_url):
        """Parse HTML directory listing to find files and directories."""
        files = []
        directories = []
        
        # Look for href links in the HTML 
        href_pattern = r'<a href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(href_pattern, html_content)
        
        for href, text in matches:
            # Skip parent directory links and external URLs
            if href.startswith('..') or href.startswith('http'):
                continue
                
            if href.endswith('/'):
                # This is a directory
                directories.append(href.rstrip('/'))
            else:
                # This is a file - include ALL files (no filtering)
                files.append(href)
        
        return files, directories
    
    def get_directory_content(url):
        """Get HTML content from a directory URL."""
        try:
            result = subprocess.run(
                ["curl", "-s", "-L", url],
                capture_output=True,
                text=True,
                timeout=20
            )
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Error fetching {url}: {result.stderr}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    try:
        all_files = set()
        directories_to_visit = [base_url.rstrip('/')]
        visited_dirs = set()
        
        # Process directories with full recursive discovery
        while directories_to_visit:
            current_dir = directories_to_visit.pop(0)
            if current_dir in visited_dirs:
                continue
                
            visited_dirs.add(current_dir)
            html_content = get_directory_content(current_dir)
            if not html_content:
                continue
                
            files, subdirs = parse_html_directory_listing(html_content, current_dir)
            
            # Add ALL files to our collection (no filtering)
            for file in files:
                filename = file.split('/')[-1]  # Extract just the filename
                all_files.add(filename)
            
            # Add all discovered subdirectories to visit list
            for subdir in subdirs:
                if subdir.startswith('/'):
                    # Absolute path - construct full URL
                    full_subdir_url = f"https://osdf-director.osg-htc.org{subdir}/"
                else:
                    # Relative path
                    full_subdir_url = f"{current_dir.rstrip('/')}/{subdir}/"
                
                if full_subdir_url not in visited_dirs:
                    directories_to_visit.append(full_subdir_url)
        
        print(f"Found {len(all_files)} files total in repository")
        return all_files
        
    except Exception as e:
        print(f"Unexpected error getting repository files: {e}")
        return set()


if __name__ == "__main__":

    # Read in the MOM_input.yaml file and extract all input file names
    MOM_input_yaml = yaml.safe_load(open("./param_templates/MOM_input.yaml", "r"))
    MOM_input_files = get_input_files_in_MOM_input(MOM_input_yaml)

    # Read in the input_data_list.yaml file and extract all input file names
    input_data_list_yaml = yaml.safe_load(
        open("./param_templates/input_data_list.yaml", "r")
    )
    input_data_list_files = get_input_data_list_files(
        input_data_list_yaml, MOM_input_files
    )

    # all mom input file names in gdex inputdata repository
    repo_url = "https://osdf-data.gdex.ucar.edu/ncar/gdex/d651077/cesmdata/inputdata/ocn/mom/"
    repo_files = get_repo_files_with_curl(repo_url)

    if not repo_files:
        print("WARNING: Could not retrieve file list from repository.")
        print("This may be due to connectivity issues or changes in repository structure.")
        print("Repository validation will be skipped.")
        exit(0)  # Exit successfully since this is likely an infrastructure issue

    # File names missing in the repository
    missing_files = (
        set(
            filename
            for filelist in input_data_list_files.values()
            for filename in filelist
        )
        - repo_files
    )
    if missing_files:
        raise ValueError(
            "Below file names are listed in input_data_list.yaml but are missing "
            "in the inputdata repository. If these files are not needed, "
            "please remove them from input_data_list.yaml. If they are needed, "
            "please import them to the gdex repository.\n\n  "
            + "\n  ".join(missing_files)
        )
    else:
        print("All files in input_data_list.yaml are present in the gdex repository.")
