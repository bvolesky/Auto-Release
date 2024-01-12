import os
import subprocess
import threading
import urllib.request
import getpass
import json
from collections import OrderedDict


def get_git_tags():
    git_tags = subprocess.check_output(["git", "tag"]).decode("utf-8").strip()
    return git_tags


def delete_git_tag(tag_name):
    git_tag_delete_output = os.system('git tag -d "{}"'.format(tag_name))
    return git_tag_delete_output == 0


def push_deleted_tag_to_origin(tag_name):
    tag_push_origin_output = os.system("git push origin :refs/tags/" + tag_name)
    return tag_push_origin_output == 0


def handle_successful_rollback():
    print("NO TAGS TO DELETE\n\nSUCCESSFULLY ROLLED BACK")


def handle_failed_rollback(rollback_output):
    print(rollback_output)


def get_tag():
    while True:
        tag_prompt = input(
            "Yikes prepare failed...Paste the tag name here or type none: "
        ).strip()

        if tag_prompt != "":
            break
    return tag_prompt


def rollback():
    rollback_output = os.system("mvn clean release:rollback")

    if rollback_output != 0:
        handle_failed_rollback(rollback_output)
        return

    git_tags = get_git_tags()

    if not git_tags:
        handle_successful_rollback()
        return

    print("\n\n\n----- GIT TAGS -----")
    print(git_tags)
    print("\n--------------------\n\n")

    tag_prompt = get_tag()

    if tag_prompt == "none":
        return

    if delete_git_tag(tag_prompt):
        if push_deleted_tag_to_origin(tag_prompt):
            print("SUCCESSFULLY ROLLED BACK")
        else:
            print("Failed to push the deleted tag to origin")
    else:
        print("Failed to delete the specified tag")


def get_project_url(
    index, iterable, mapping_name, path, mnemonic_input, source_id, dataset_id
):
    max_version_dict = {}
    group_page = urllib.request.urlopen(iterable[index]).read().split("\n")

    for group_page_line in group_page:
        project_url = extract_project_url(group_page_line)

        if is_valid_url(group_page_line, mapping_name, project_url):
            version_page = urllib.request.urlopen(project_url).read().split("\n")

            for version_page_line in version_page:
                if is_valid_url(version_page_line):
                    store_max_version_from_line(max_version_dict, version_page_line)

            process_path(dataset_id, max_version_dict, mnemonic_input, path, source_id)


def extract_project_url(line):
    return line.split('<td><a href="')[-1].split('">')[0]


def is_valid_url(line, mapping_name, url):
    base_url = '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/'
    return base_url in line and mapping_name == url.split("/")[-2]


def store_max_version_from_line(max_version_dict, version_page_line):
    try:
        if float(
            version_page_line.split('<td><a href="')[-1].split('">')[0].split("/")[-2]
        ):
            max_version_dict[
                int(
                    version_page_line.split('<td><a href="')[-1]
                    .split('">')[0]
                    .split("/")[-2]
                    .split(".")[-1]
                )
            ] = version_page_line.split('<td><a href="')[-1].split('">')[0]
    except:
        pass


def process_path(dataset_id, max_version_dict, mnemonic_input, path, source_id):
    page = urllib.request.urlopen(
        max_version_dict[max(max_version_dict.keys())]).read().decode().split("\n")

    for page_line in page:
        if is_valid_jar_url(page_line):
            update_jar_url_in_config_files(page_line, dataset_id, mnemonic_input, path,
                                           source_id)


def is_valid_jar_url(line):
    base_url = '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/'
    jar_file_parts = \
    line.split('<td><a href="')[-1].split('">')[0].split("/")[-1].split("-")[-1].split(
        ".")

    return base_url in line and len(jar_file_parts) == 3 and "jar" in jar_file_parts[-1]


def update_jar_url_in_config_files(page_line, dataset_id, mnemonic_input, path,
                                   source_id):
    global new_jar
    new_jar = extract_jar_url(page_line)
    config_version = get_config_version(new_jar)
    spec_version = get_spec_version(new_jar)

    for item in os.listdir(os.path.join(path, "roles", "navi")):
        if mnemonic_input == item.replace("navi_", "").replace(
                "_source_registry_config.json", ""):
            file_path = os.path.join(path, "roles", "navi", item)
            update_config_file(file_path, dataset_id, source_id, spec_version, new_jar,
                               config_version)


def extract_jar_url(line):
    return line.split('<td><a href="')[-1].split('">')[0]


def get_config_version(url):
    return url.split("/")[-2]


def get_spec_version(url):
    return url.split("/")[-3].split("_")[-1].replace("v", "")


def update_config_file(file_path, dataset_id, source_id, spec_version, new_jar,
                       config_version):
    with open(file_path) as naviJSONFile:
        naviJSONFileDict = json.load(naviJSONFile, object_pairs_hook=OrderedDict)

    cID = list(naviJSONFileDict["default_attributes"]["source_registry_cookbook"][
                   "DISCOVERY"].keys())[0].strip()
    data_set = \
    naviJSONFileDict["default_attributes"]["source_registry_cookbook"]["DISCOVERY"][
        cID]["data_sources"][source_id]["data_sets"][dataset_id]["spec_versions"][
        spec_version]
    data_set["mapping_jar_url"] = new_jar
    data_set["mapping_config_version"] = config_version

    with open(file_path, "w") as naviJSONFileOut:
        json.dump(naviJSONFileDict, naviJSONFileOut, indent=2, separators=(",", ": "))


def multi_thread(iterable, function, *args):
    threads = []
    for _index in range(len(iterable)):
        x = threading.Thread(target=function, args=(_index, iterable, *args))
        threads.append(x)
        x.start()
    for thread in threads:
        thread.join()


def update_release_jar(
    mappings_page, mapping_name, path, mnemonic_input, source_id, dataset_id
):
    print("Updating release jar automatically!")
    repo_group_list = []
    for mappings_page_line in mappings_page:
        if (
            '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/'
            in mappings_page_line
        ):
            repo_group_list.append(
                mappings_page_line.split('<td><a href="')[-1].split('">')[0]
            )
    multi_thread(
        repo_group_list,
        get_project_url,
        mapping_name,
        path,
        mnemonic_input,
        source_id,
        dataset_id,
    )


def change_working_directory(path):
    os.chdir(path)


def get_user_inputs():
    mnemonic_input = input("Enter github mnemonic: ").strip().lower()
    source_id = input("Enter source id: ").strip()
    dataset_id = input("Enter dataset id: ").strip()
    datasink_filepath = input("Enter datasink file path: ").strip()
    merge_request = input("Enter merge request url: ").strip()
    ticket_number = input("Enter tnt number: ").strip()
    return (
        mnemonic_input,
        source_id,
        dataset_id,
        datasink_filepath,
        merge_request,
        ticket_number,
    )


def get_yuna_password():
    while True:
        password_check1 = getpass.getpass("Enter yuna password: ")
        password_check2 = getpass.getpass("Confirm yuna password: ")
        if password_check1 == password_check2:
            return password_check1
        else:
            print("Passwords do not match, try again")


def get_mappings_page():
    mappings_url = "http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/"
    mappings_page = urllib.request.urlopen(mappings_url).read().decode().split("\n")
    return mappings_page


def generate_commands(mnemonic_input, source_id, datasink_filepath):
    gen_commands_1 = f"python /opt/data_acquisition/tools/ezdeploy/sourcedeploy.py -m {mnemonic_input} -s {source_id}\npython /opt/data_acquisition/tools/ezdryrun/ezdryrun.py -e -r -s -m {mnemonic_input} -f {datasink_filepath}\n"
    gen_commands_2 = 'cat $(find . -name "ekcdeets*" | tail -n -1)\n\n'
    return gen_commands_1, gen_commands_2


def get_gitlab_ssh_url():
    while True:
        prepare_prompt = input("Enter gitlab ssh: ").strip()
        if "git@gitlab.cernersphere.net:" in prepare_prompt:
            return prepare_prompt


def clone_git_repository(prepare_prompt, user_profile):
    mapping_name = prepare_prompt.split("/")[1].split(".")[0]
    temp_dir = os.path.join(user_profile, f"RELEASE_{mapping_name}")

    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    os.chdir(temp_dir)
    pull_output = os.system(f'git clone "{prepare_prompt}"')
    return pull_output, temp_dir, mapping_name


def perform_release(mapping_name):
    os.chdir(mapping_name)
    prepare_output = os.system("mvn -B clean release:prepare")
    if prepare_output == 0:
        release_output = os.system("mvn release:perform -Dgoals=deploy")
        if release_output == 0:
            print("SUCCESSFULLY RELEASED")
        else:
            print(release_output)
            rollback()
    else:
        rollback()


def add_commit_push_changes(path, ticket_number):
    os.chdir(path)
    anotha_pull = os.system("git pull")

    if anotha_pull == 0:
        add_output = os.system("git add -A")
        if add_output == 0:
            commit_output = os.system(
                'git commit -u -m "DAHLTHNTNT-{}"'.format(ticket_number)
            )
            if commit_output == 0:
                push_output = os.system("git push -u origin master")


def write_generated_commands_to_files(gen_commands_1, gen_commands_2, user_profile):
    with open(os.path.join(user_profile, "remote_commands.txt"), "w") as rc:
        rc.writelines(gen_commands_1)
    with open(os.path.join(user_profile, "remote_commands2.txt"), "w") as rc2:
        rc2.writelines(gen_commands_2)


def execute_remote_commands(username, password, user_profile):
    path = os.path.join(user_profile, "remote_commands.txt")
    path2 = os.path.join(user_profile, "remote_commands2.txt")
    node = f"{username}@utility-data-integration.yuna.us-zone1.healtheintent.net"
    command_1 = f"plink.exe -ssh {node} -pw {password} -m {path} -batch"
    remote_command_output = os.system(command_1)

    if remote_command_output == 0:
        proc = subprocess.Popen(
            [
                "plink.exe",
                "-ssh",
                f"{node}",
                "-pw",
                f"{password}",
                "-m",
                f"{path2}",
                "-batch",
            ],
            stdout=subprocess.PIPE,
            shell=True,
        )
        (rc_output, err) = proc.communicate()

    return rc_output


def modify_output_and_write_to_file(rc_output, new_jar, merge_request, user_profile):
    # Initialize variables
    target_index = 0
    new_rc_output = ""

    # Iterate through lines in rc_output
    for line in rc_output.split("\n"):
        if "||Local File Path: | |" in line:
            line = f"||Local File Path: |{new_jar}|"
        elif "||Merge Request: | |" in line:
            line = f"||Merge Request: |{merge_request}|"
        new_rc_output += line + "\n"

    # Find the target index
    for index, line in enumerate(new_rc_output.split("\n")):
        if "h3.Release Stats:" in line:
            target_index = index

    # Extract the relevant part of rc_output
    new_rc_output = "\n".join(new_rc_output.split("\n")[target_index:])

    # Write the modified output to a file in user_profile directory
    with open(os.path.join(user_profile, "ezdryrun_stats.txt"), "w") as o:
        o.write(new_rc_output)


def delete_temp_files(path, path2):
    os.system(f"del -f {path}")
    os.system(f"del -f {path2}")


def open_output_file(user_profile):
    os.startfile(os.path.join(user_profile, "ezdryrun_stats.txt"))


def main():
    # Change the working directory
    path = "C:\\Users\\bv083283\\GitHub\\data-integration_chef-repo"
    change_working_directory(path)

    # Get user inputs
    (
        mnemonic_input,
        source_id,
        dataset_id,
        datasink_filepath,
        merge_request,
        ticket_number,
    ) = get_user_inputs()

    # Get Yuna password
    password = get_yuna_password()

    # Get mappings page
    mappings_page = get_mappings_page()

    # Generate commands
    gen_commands_1, gen_commands_2 = generate_commands(
        mnemonic_input, source_id, datasink_filepath
    )

    # Get GitLab SSH URL
    prepare_prompt = get_gitlab_ssh_url()

    # Clone Git repository
    pull_output, temp_dir, mapping_name = clone_git_repository(
        prepare_prompt, os.environ["USERPROFILE"]
    )

    # Perform release if cloning was successful
    if pull_output == 0:
        perform_release(mapping_name)
    else:
        print(pull_output)

    # Update release jar
    update_release_jar(
        mappings_page, mapping_name, path, mnemonic_input, source_id, dataset_id
    )

    # Add, commit, and push changes to the repository
    add_commit_push_changes(path, ticket_number)

    # Write generated commands to files
    write_generated_commands_to_files(
        gen_commands_1, gen_commands_2, os.environ["USERPROFILE"]
    )

    # Execute remote commands and capture their output
    rc_output = execute_remote_commands(
        os.environ["USERNAME"], password, os.environ["USERPROFILE"]
    )

    # Modify output and write to a file
    modify_output_and_write_to_file(
        rc_output, new_jar, merge_request, os.environ["USERPROFILE"]
    )

    # Delete temporary files
    delete_temp_files(
        os.path.join(os.environ["USERPROFILE"], "remote_commands.txt"),
        os.path.join(os.environ["USERPROFILE"], "remote_commands2.txt"),
    )

    # Open the output file
    open_output_file(os.environ["USERPROFILE"])


if __name__ == "__main__":
    main()
