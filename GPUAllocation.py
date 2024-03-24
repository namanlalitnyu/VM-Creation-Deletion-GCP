import subprocess
import json
import re

# Error patterns which happen while VM creation.
error_pattern1 = r"The resource '[^']*' was not found"
error_pattern2 = r"Machine type with name '[^']*' does not exist in zone"

# List of GPUs for the assignment.
gpu_types = ['nvidia-tesla-t4']
print("GPUs: ", gpu_types)

# Funtion used to fetch the all the regions
def fetch_regions(command):
    result = subprocess.run(command, text=True, capture_output=True, shell=True)
    if result.returncode == 0:
        return result.stdout
    else:
        return None

# Function to execute the commands in Google Cloud
def run_command(command):
    print("Entered run_command function", command)
    result = subprocess.run(command, text=True, capture_output=True, shell=True)
    if result.returncode == 0:
        return {
            "GPU_Available" : "Yes",
            "VM_Created": "Yes",
            "Output": result.stdout
        }
    else:
        if(re.search(error_pattern1, result.stderr) or re.search(error_pattern2, result.stderr)):
            return {
                "GPU_Available" : "No",
                "VM_Created": "No",
                "Output": result.stderr
            }
        else:
            return {
                "GPU_Available" : "Yes",
                "VM_Created": "No",
                "Output": result.stderr
            }
    

# Get the list of all regions
regions_command = "gcloud compute regions list --format=json"
regions_output = fetch_regions(regions_command)
regions = json.loads(regions_output)

# For this assignment, we will only focus on the us-regions to save time and resources
us_regions = []

# Print the number of regions and zones with them
print("Number of Regions: ", len(regions))
for region in regions:
    print("Region Name:- " + str(region['name']) + " ; Zones:- " + str(len(region['zones'])))
    
    # Filter the US Regions
    if('us-' in region['name']):
        us_regions.append(region)

# Results table
results = []

# Iterate through each region and its zones, and try to create the Virtual Machine with GPU
for region in us_regions:
    for zone in region['zones']:
        zone_name = zone.split('/')[-1]
        for gpu_type in gpu_types:
            print("Region Name:- ", region['name'])
            print("Zone Name:- ", zone_name)
            print("GPU Name:- ", gpu_type)

            # Attempt to create a VM with a GPU in this zone
            vm_name = f"test-vm-{zone_name}-{gpu_type.replace('-', '')}"            
            create_vm_command = f"gcloud compute instances create {vm_name} --zone={zone_name} --machine-type=n1-standard-1 --accelerator type={gpu_type},count=1 --create-disk=auto-delete=yes,boot=yes,device-name={vm_name},image=projects/ml-images/global/images/c0-deeplearning-common-cu113-v20230925-debian-10,mode=rw,size=50,type=projects/core-verbena-328218/zones/{zone_name}/diskTypes/pd-balanced --maintenance-policy TERMINATE --restart-on-failure --format=json"
            vm_output = run_command(create_vm_command)
            
            if vm_output["VM_Created"] == "Yes":
                # VM created successfully
                print("Virtual Machine with CUDA image created successfully!", vm_output["Output"])
                results.append((zone_name, gpu_type, vm_output["GPU_Available"], vm_output["VM_Created"]))
                
                # Delete the VM after creation to avoid wastage of resources
                print("Deleting the Virtual Machine")
                delete_vm_command = f"gcloud compute instances delete {vm_name} --zone={zone_name} --quiet"
                run_command(delete_vm_command)
            else:
                # VM creation failed
                print("Virtual Machine with CUDA image failed!", vm_output["Output"])
                results.append((zone_name, gpu_type, vm_output["GPU_Available"], vm_output["VM_Created"]))

# Print results
print(f"{'Zone':<20} {'GPU Type':<20} {'GPU Available':<15} {'GPU Allocated to VM':<20}")
for result in results:
    print(f"{result[0]:<20} {result[1]:<20} {result[2]:<15} {result[3]:<20}")