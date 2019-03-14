#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

sys.path.append(os.path.join(sys.path[0], "../", "lib"))
import squad_client


def cancel_lava_jobs(url, project, build_version, identity=None):
    """
        Requires lavacli. If using a non-default lava identity, specify the identity
        string in 'identity'.

        Given something like the following:
            url="https://qa-reports.linaro.org"
            project="linux-stable-rc-4.9-oe"
            build="v4.9.162-94-g0384d1b03fc9"

        Discover and cancel all lava jobs that are still running.

        Note this doesn't handle duplicate project names well..
    """

    base_url = squad_client.urljoiner(url, "api/projects/")

    params = {"slug": project}
    try:
        project = squad_client.get_objects(base_url, False, params)[0]
    except:
        exit("Error: project {} not found at {}".format(project, base_url))
    build_list = squad_client.get_objects(project["builds"], {"version": build_version})
    identity_argument = ""
    if identity:
        identity_argument = "-i {}".format(identity)
    for build in build_list:
        if build["version"] != build_version:
            # double check. but also, version filter is broken presently
            continue

        testjobs = squad_client.get_objects(build["testjobs"])
        for testjob in testjobs:
            if testjob["job_status"] != "Submitted":
                print(
                    "Skipping: %s; status: %s"
                    % (testjob["job_id"], testjob["job_status"])
                )
                continue
            backend = squad_client.get_objects(testjob["backend"])
            print("Canceling: %s" % (testjob["job_id"]))

            cmd = "lavacli {} jobs cancel {}".format(
                identity_argument, testjob["job_id"]
            )
            print(cmd)
            subprocess.check_call(cmd, shell=True)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Cancel LAVA jobs from a specific SQUAD build.",
        epilog="""
Example usage:
    cancel_squad_testjobs.py "https://qa-reports.linaro.org/lkft/linux-stable-rc-4.9-oe/build/v4.9.162-94-g0384d1b03fc9/"
""",
    )
    parser.add_argument(
        "--identity", "-i", dest="identity", default=None, help="lavacli identity"
    )
    parser.add_argument("build_url", help="URL of the build")

    args = parser.parse_args()

    try:
        (
            url,
            group,
            project,
            build_version,
        ) = squad_client.get_squad_params_from_build_url(args.build_url)
    except:
        sys.exit("Error parsing url: {}".format(args.build_url))

    cancel_lava_jobs(url, project, build_version, args.identity)
