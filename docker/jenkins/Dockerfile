FROM eclipse-temurin:11.0.22_7-jdk-jammy as jre-build

# Create a custom Java runtime
RUN jlink \
    --add-modules ALL-MODULE-PATH \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output /javaruntime

# Main Jenkins image
FROM ubuntu:jammy-20240111

# Environment variables
ENV LANG C.UTF-8
ENV JENKINS_HOME /var/jenkins_home
ENV JENKINS_SLAVE_AGENT_PORT 50000
ENV JENKINS_VERSION 2.426.1
ENV JENKINS_UC https://updates.jenkins.io
ENV JENKINS_UC_EXPERIMENTAL=https://updates.jenkins.io/experimental
ENV JENKINS_INCREMENTALS_REPO_MIRROR=https://repo.jenkins-ci.org/incrementals
ENV COPY_REFERENCE_FILE_LOG $JENKINS_HOME/copy_reference_file.log
ENV JAVA_HOME /opt/java/openjdk

# Jenkins is run with user `jenkins`, uid = 1000
ARG user=jenkins
ARG group=jenkins
ARG uid=1000
ARG gid=1000

# Install required packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        openssh-client \
        unzip \
        tzdata \
        fontconfig \
        locales \
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create Jenkins user and group
RUN groupadd -g ${gid} ${group} \
    && useradd -d "$JENKINS_HOME" -u ${uid} -g ${gid} -m -s /bin/bash ${user}

# Copy custom Java runtime
COPY --from=jre-build /javaruntime $JAVA_HOME

# Install Jenkins
RUN curl -fsSL https://get.jenkins.io/war/${JENKINS_VERSION}/jenkins.war -o /usr/share/jenkins/jenkins.war \
    && chown -R ${user}:${group} /usr/share/jenkins

# Install Jenkins plugins
COPY docker/jenkins/plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Copy configuration scripts
COPY docker/jenkins/scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Switch to Jenkins user
USER ${user}

# Create directories
RUN mkdir -p ${JENKINS_HOME}/init.groovy.d

# Copy init scripts and configurations
COPY --chown=${user}:${group} docker/jenkins/init.groovy.d/ ${JENKINS_HOME}/init.groovy.d/
COPY --chown=${user}:${group} docker/jenkins/config/ ${JENKINS_HOME}/config/

# Expose ports
EXPOSE 8080 ${JENKINS_SLAVE_AGENT_PORT} 50000

# Set volume
VOLUME ${JENKINS_HOME}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=1m --retries=3 \
    CMD curl -f http://localhost:8080/login || exit 1

# Start Jenkins
COPY docker/jenkins/jenkins-support /usr/local/bin/jenkins-support
COPY docker/jenkins/jenkins.sh /usr/local/bin/jenkins.sh
ENTRYPOINT ["/usr/local/bin/jenkins.sh"]