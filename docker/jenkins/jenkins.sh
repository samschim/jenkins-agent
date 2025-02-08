#!/usr/bin/env bash

set -e

# Source function library
. /usr/local/bin/jenkins-support

# Copy files from /usr/share/jenkins/ref into $JENKINS_HOME
# So the initial JENKINS-HOME is set with expected content.
# Don't override, as this is just a reference setup, and use from UI
# can then change this, upgrade plugins, etc.
copy_reference_file() {
    f="${1%/}"
    b="${f%.override}"
    rel="${b:23}"
    version_marker="${rel}.version_from_image"
    dir=$(dirname "${b}")
    local action;
    local reason;
    local container_version;
    local image_version;
    local marker_version;
    local log;
    container_version=$(cat "${JENKINS_HOME}/${version_marker}" 2>/dev/null)
    image_version=$(cat "${f}" 2>/dev/null)
    log=",${rel},${image_version},${container_version},"

    if [[ ! -e "${JENKINS_HOME}/${rel}" ]]; then
        action="INSTALLED"
        log="${log}${action},"
        reason="Initial install"
        mkdir -p "${JENKINS_HOME}/${dir:23}"
        cp -pr "${f}" "${JENKINS_HOME}/${rel}";
        # pin plugins on initial copy
        touch "${JENKINS_HOME}/${version_marker}"
        echo "${image_version}" > "${JENKINS_HOME}/${version_marker}"
        if [[ "${rel}" == plugins/*.jpi ]]; then
            touch "${JENKINS_HOME}/${rel}.pinned"
        fi
    else
        action="SKIPPED"
        log="${log}${action},"
        reason="Installed version"
    fi
    echo "${f} ${action}: ${reason}" >> "$COPY_REFERENCE_FILE_LOG"
}

# Set Jenkins home directory permissions
chown -R jenkins:jenkins "$JENKINS_HOME"

# If first argument is "jenkins", run Jenkins
if [[ "$1" == "jenkins" ]]; then
    # Read JAVA_OPTS and JENKINS_OPTS into arrays to avoid need for eval
    java_opts_array=()
    while IFS= read -r JAVA_OPT; do
        java_opts_array+=("$JAVA_OPT")
    done < <([[ $JAVA_OPTS ]] && xargs printf '%s\n' <<<"$JAVA_OPTS")

    jenkins_opts_array=()
    while IFS= read -r JENKINS_OPT; do
        jenkins_opts_array+=("$JENKINS_OPT")
    done < <([[ $JENKINS_OPTS ]] && xargs printf '%s\n' <<<"$JENKINS_OPTS")

    exec java "${java_opts_array[@]}" -jar /usr/share/jenkins/jenkins.war "${jenkins_opts_array[@]}" "$@"
fi

# If argument is not jenkins, run it
exec "$@"