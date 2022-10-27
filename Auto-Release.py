# Import Modules
import os
import cmd
import urllib
import threading
import json
from collections import OrderedDict
import subprocess
import getpass


cli = cmd.Cmd()
path = "C:\\Users\\bv083283\\GitHub\\data-integration_chef-repo"
os.chdir(path)
repo_group_list = []
repo_project_list = []
os.system("git pull")
new_jar = ''
mnemonic_input = raw_input("Enter github mnemonic: ").strip().lower()
source_id = raw_input("Enter source id: ").strip()
dataset_id = raw_input("Enter dataset id: ").strip()
datasink_filepath = raw_input('Enter datasink file path: ').strip()
merge_request = raw_input('Enter merge request url: ').strip()
ticket_number = raw_input('Enter tnt number: ').strip()
while True:
    password_check1 = getpass.getpass("Enter yuna password: ")
    password_check2 = getpass.getpass("Confirm yuna password: ")
    if password_check1 != password_check2:
        print("Passwords do not match, try again")
    else:
        password = password_check1
        break
mappings_url = 'http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/'
mappings_page = urllib.urlopen(mappings_url).read().split('\n')
username = os.environ['USERNAME']
user_profile = os.environ['USERPROFILE']
gen_commands_1 = 'python /opt/data_acquisition/tools/ezdeploy/sourcedeploy.py -m {} -s {}\npython /opt/data_acquisition/tools/ezdryrun/ezdryrun.py -e -r -s -m {} -f {}\n'.format(mnemonic_input, source_id, mnemonic_input, datasink_filepath)
gen_commands_2 = 'cat $(find . -name "ekcdeets*" | tail -n -1)\n\n'


def rollback():
    global rollback_output, git_tag_output, tag_prompt, git_tag_delete_output, tag_push_origin_output
    rollback_output = os.system('mvn clean release:rollback')
    if rollback_output == 0:
        proc = subprocess.Popen(["git", "tag"], stdout=subprocess.PIPE, shell=True)
        (git_tags, err) = proc.communicate()
        git_tag_output = os.system('git tag')
        if git_tags != "":
            print('\n\n\n----- GIT TAGS -----')
            git_tag_output = os.system('git tag')
            print(git_tag_output)
            print('\n--------------------\n\n')
            while True:
                tag_prompt = raw_input("Yikes prepare failed...Paste the tag name here or type none: ").strip()
                if tag_prompt != "":
                    break
            if tag_prompt == 'none':
                return
            git_tag_delete_output = os.system('git tag -d "{}"'.format(tag_prompt))
            if git_tag_delete_output == 0:
                tag_push_origin_output = os.system('git push origin :refs/tags/' + tag_prompt)
                if tag_push_origin_output == 0:
                    print("SUCCESSFULLY ROLLED BACK")
                else:
                    print(tag_push_origin_output)
            else:
                print(git_tag_delete_output)
        else:
            print("NO TAGS TO DELETE\n\nSUCCESSFULLY ROLLED BACK")
    else:
        print(rollback_output)


def getProjectUrl(_index, _iterable):
    import json
    global new_jar
    max_version_dict = {}
    group_page = urllib.urlopen(_iterable[_index]).read().split('\n')
    for group_page_line in group_page:
        project_url = group_page_line.split('<td><a href="')[-1].split('">')[0]
        if '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/' in group_page_line and mapping_name == project_url.split('/')[-2]:
            version_page = urllib.urlopen(project_url).read().split('\n')
            for version_page_line in version_page:
                if '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/' in version_page_line:
                    try:
                        if float(version_page_line.split('<td><a href="')[-1].split('">')[0].split('/')[-2]):
                            max_version_dict[int(version_page_line.split('<td><a href="')[-1].split('">')[0].split('/')[-2].split('.')[-1])] = version_page_line.split('<td><a href="')[-1].split('">')[0]
                    except:
                        pass
            bingpot_page = urllib.urlopen(max_version_dict[max(max_version_dict.keys())]).read().split('\n')
            for bingpot_page_line in bingpot_page:
                if (
                        '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/'
                        in bingpot_page_line
                        and len(bingpot_page_line.split('<td><a href="')[-1]
                                        .split('">')[0]
                                        .split('/')[-1]
                                        .split('-')[-1]
                                        .split('.')
                                )
                        == 3
                        and 'jar'
                        in bingpot_page_line.split('<td><a href="')[-1]
                        .split('">')[0]
                        .split('/')[-1]
                        .split('-')[-1]
                        .split('.')[-1]
                ):
                    new_jar = bingpot_page_line.split('<td><a href="')[-1].split('">')[0]
                    config_version = new_jar.split('/')[-2]
                    spec_version = new_jar.split('/')[-3].split('_')[-1].replace("v", "")
                    for item in os.listdir(path + "\\roles\\navi"):
                        if mnemonic_input == item.replace("navi_", '').replace('_source_registry_config.json', ''):
                            file = item
                            file_path = path + "\\roles\\navi\\" + file

                            with open(file_path) as naviJSONFile:
                                naviJSONFileDict = json.load(naviJSONFile, object_pairs_hook=OrderedDict)
                                naviJSONFile.close()
                            a = naviJSONFileDict["default_attributes"]["source_registry_cookbook"]["DISCOVERY"]
                            cID = a.keys()[0].strip()
                            naviJSONFileDict["default_attributes"]["source_registry_cookbook"]["DISCOVERY"][cID]["data_sources"][source_id]["data_sets"][dataset_id]["spec_versions"][spec_version]["mapping_jar_url"] = new_jar
                            naviJSONFileDict["default_attributes"]["source_registry_cookbook"]["DISCOVERY"][cID]["data_sources"][source_id]["data_sets"][dataset_id]["spec_versions"][spec_version]["mapping_config_version"] = config_version

                            with open(file_path, 'w') as naviJSONFileOut:
                                json.dump(naviJSONFileDict, naviJSONFileOut, indent=2, separators=(',', ': '))
                                naviJSONFileOut.close()


def MultiThread(_iterable, _function):
    threads = []
    for _index in range(len(_iterable)):
        x = threading.Thread(target=_function, args=(_index, _iterable))
        threads.append(x)
        x.start()
    for thread in threads:
        thread.join()


def updateJSONWithReleaseJar():
    for mappings_page_line in mappings_page:
        if '<a href="http://repo.release.cerner.corp/nexus/content/repositories/datawx-repo/com/cerner/pophealth/mappings/' in mappings_page_line:
            repo_group_list.append(mappings_page_line.split('<td><a href="')[-1].split('">')[0])
    MultiThread(repo_group_list, getProjectUrl)


while True:
    prepare_prompt = raw_input('Enter gitlab ssh: ').strip()
    if 'git@gitlab.cernersphere.net:' in prepare_prompt:
        break
mapping_name = prepare_prompt.split('/')[1].split('.')[0]
temp_dir = user_profile + '\RELEASE_' + mapping_name
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)
os.chdir(temp_dir)
pull_output = os.system('git clone "{}"'.format(prepare_prompt))

if pull_output == 0:
    os.chdir(mapping_name)
    prepare_output = os.system('mvn -B clean release:prepare')
    if prepare_output == 0:
        release_output = os.system('mvn release:perform -Dgoals=deploy')
        if release_output == 0:
            print("SUCCESSFULLY RELEASED")
        else:
            print(release_output)
            rollback()
    else:
        rollback()
else:
    print(pull_output)
os.chdir(user_profile)
os.system('rmdir /S /Q "{}"'.format(temp_dir))
print("Updating release jar automatically!")
updateJSONWithReleaseJar()
os.chdir(path)
anotha_pull = os.system('git pull')
if anotha_pull == 0:
    add_output = os.system('git add -A')
    if add_output == 0:
        commit_output = os.system('git commit -u -m "DAHLTHNTNT-{}"'.format(ticket_number))
        if commit_output == 0:
            push_output = os.system('git push -u origin master')

os.chdir(user_profile)
with open('remote_commands.txt', 'w') as rc:
    rc.writelines(gen_commands_1)
with open('remote_commands2.txt', 'w') as rc2:
    rc2.writelines(gen_commands_2)

os.chdir("C:\Program Files\PuTTY")

rc_output = ""
new_rc_output = ""
path = user_profile + "\\" + 'remote_commands.txt'
path2 = user_profile + "\\" + 'remote_commands2.txt'
node = '{}@utility-data-integration.yuna.us-zone1.healtheintent.net'.format(username)
command_1 = 'plink.exe -ssh {} -pw {} -m {} -batch'.format(node, password, path)
remote_command_output = os.system(command_1)
if remote_command_output == 0:
    proc = subprocess.Popen(['plink.exe', '-ssh', '{}'.format(node), '-pw', '{}'.format(password), '-m', '{}'.format(path2), '-batch'], stdout=subprocess.PIPE, shell=True)
    (rc_output, err) = proc.communicate()
target_index = 0
os.chdir(user_profile)
all_lines = ""
new_jar_r = new_jar
for line in rc_output.split('\n'):
    if '||Local File Path: | |' in line:
        line = '||Local File Path: |' + new_jar + '|'
    if '||Merge Request: | |' in line:
        line = '||Merge Request: |' + merge_request + '|'
    all_lines += (line+'\n')

for index in range(len(all_lines.split('\n'))):
    if 'h3.Release Stats:' in all_lines.split('\n')[index]:
        target_index = index
new_rc_output = '\n'.join(str(x) for x in all_lines.split('\n')[target_index:])
os.chdir(user_profile)
with open('ezdryrun_stats.txt', 'w') as o:
    o.write(new_rc_output)

os.chdir(user_profile)
os.system('del -f {}'.format(path))
os.system('del -f {}'.format(path2))

os.startfile('ezdryrun_stats.txt')
