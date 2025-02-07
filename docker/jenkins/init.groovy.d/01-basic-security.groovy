#!groovy

import jenkins.model.*
import hudson.security.*
import jenkins.security.s2m.AdminWhitelistRule

def instance = Jenkins.getInstance()

// Disable Setup Wizard
instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)

// Configure Security
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// Create admin user
if (!hudsonRealm.getAllUsers().find { it.id == 'admin' }) {
    def adminPassword = System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin'
    hudsonRealm.createAccount('admin', adminPassword)
}

// Configure Agent Protocol
Set<String> agentProtocolsList = ['JNLP4-connect', 'Ping']
if(!instance.getAgentProtocols().equals(agentProtocolsList)) {
    instance.setAgentProtocols(agentProtocolsList)
}

// Configure CSRF Protection
instance.setCrumbIssuer(new hudson.security.csrf.DefaultCrumbIssuer(true))

// Configure Slave to Master Access Control
Jenkins.instance.getInjector().getInstance(AdminWhitelistRule.class).setMasterKillSwitch(false)

// Save configuration
instance.save()