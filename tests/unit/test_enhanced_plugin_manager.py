"""Unit tests for enhanced plugin manager agent."""
import pytest
from unittest.mock import AsyncMock, patch
from langchain_jenkins.agents.enhanced_plugin_manager import (
    EnhancedPluginManager,
    PluginInfo,
    SecurityIssue
)

@pytest.fixture
def plugin_manager():
    """Create a plugin manager for testing."""
    manager = EnhancedPluginManager()
    manager.jenkins = AsyncMock()
    manager.llm = AsyncMock()
    return manager

@pytest.fixture
def sample_plugins():
    """Create sample plugin information."""
    return [
        PluginInfo(
            name="git",
            version="4.11.0",
            latest_version="4.12.0",
            dependencies=["workflow-scm-step"],
            security_warnings=[],
            enabled=True,
            pinned=False,
            url="https://plugins.jenkins.io/git"
        ),
        PluginInfo(
            name="workflow-scm-step",
            version="2.13",
            latest_version=None,
            dependencies=[],
            security_warnings=[],
            enabled=True,
            pinned=True,
            url="https://plugins.jenkins.io/workflow-scm-step"
        )
    ]

@pytest.mark.asyncio
async def test_list_plugins(plugin_manager, sample_plugins):
    """Test listing plugins."""
    plugin_manager.jenkins.get.return_value = {
        "plugins": [
            {
                "shortName": "git",
                "version": "4.11.0",
                "latestVersion": "4.12.0",
                "dependencies": [{"shortName": "workflow-scm-step"}],
                "enabled": True,
                "pinned": False,
                "url": "https://plugins.jenkins.io/git"
            },
            {
                "shortName": "workflow-scm-step",
                "version": "2.13",
                "dependencies": [],
                "enabled": True,
                "pinned": True,
                "url": "https://plugins.jenkins.io/workflow-scm-step"
            }
        ]
    }
    
    result = await plugin_manager._list_plugins()
    
    assert len(result) == 2
    assert result[0].name == "git"
    assert result[0].version == "4.11.0"
    assert result[1].name == "workflow-scm-step"
    assert result[1].pinned is True

@pytest.mark.asyncio
async def test_install_plugin(plugin_manager):
    """Test plugin installation."""
    plugin_manager._get_plugin_info = AsyncMock(return_value={
        "dependencies": []
    })
    
    result = await plugin_manager._install_plugin("git", "4.11.0")
    
    assert result["status"] == "installed"
    assert result["plugin"] == "git"
    assert result["version"] == "4.11.0"

@pytest.mark.asyncio
async def test_update_plugin(plugin_manager, sample_plugins):
    """Test plugin update."""
    plugin_manager._list_plugins = AsyncMock(return_value=sample_plugins)
    
    result = await plugin_manager._update_plugin("git", "4.12.0")
    
    assert result["status"] == "updated"
    assert result["plugin"] == "git"
    assert result["from_version"] == "4.11.0"
    assert result["to_version"] == "4.12.0"

@pytest.mark.asyncio
async def test_uninstall_plugin(plugin_manager, sample_plugins):
    """Test plugin uninstallation."""
    plugin_manager._list_plugins = AsyncMock(return_value=sample_plugins)
    
    result = await plugin_manager._uninstall_plugin("git", check_dependencies=True)
    
    assert result["status"] == "uninstalled"
    assert result["plugin"] == "git"

@pytest.mark.asyncio
async def test_check_updates(plugin_manager):
    """Test update checking."""
    plugin_manager.jenkins.get.return_value = {
        "sites": [
            {
                "updates": [
                    {
                        "name": "git",
                        "currentVersion": "4.11.0",
                        "version": "4.12.0"
                    },
                    {
                        "name": "workflow-scm-step",
                        "currentVersion": "2.13",
                        "version": "2.14",
                        "security": True,
                        "securityWarnings": ["CVE-2023-1234"]
                    }
                ]
            }
        ]
    }
    
    result = await plugin_manager._check_updates()
    
    assert result["status"] == "success"
    assert len(result["updates"]) == 1
    assert len(result["security_updates"]) == 1
    assert result["security_updates"][0]["plugin"] == "workflow-scm-step"

@pytest.mark.asyncio
async def test_scan_security(plugin_manager, sample_plugins):
    """Test security scanning."""
    plugin_manager._list_plugins = AsyncMock(return_value=sample_plugins)
    plugin_manager.jenkins.get.return_value = {
        "warnings": [
            {
                "plugin": "git",
                "severity": "high",
                "message": "Security vulnerability",
                "cve": "CVE-2023-1234",
                "fixVersion": "4.12.0"
            }
        ]
    }
    plugin_manager.llm.agenerate.return_value.generations[0].text = """{
        "issues": [],
        "recommendations": ["Update plugins"],
        "urgent_updates": ["git"],
        "best_practices": ["Enable security warnings"]
    }"""
    
    result = await plugin_manager._scan_security()
    
    assert result["status"] == "success"
    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["plugin"] == "git"
    assert result["analysis"]["urgent_updates"] == ["git"]

@pytest.mark.asyncio
async def test_resolve_dependencies(plugin_manager):
    """Test dependency resolution."""
    plugin_manager._get_plugin_info = AsyncMock(side_effect=[
        {
            "dependencies": [
                {"name": "workflow-scm-step"}
            ]
        },
        {
            "dependencies": []
        }
    ])
    
    result = await plugin_manager._resolve_dependencies(["git"])
    
    assert result["status"] == "success"
    assert "git" in result["dependencies"]
    assert "workflow-scm-step" in result["install_order"]

@pytest.mark.asyncio
async def test_check_compatibility(plugin_manager):
    """Test compatibility checking."""
    plugin_manager.jenkins.get.return_value = {"version": "2.375.3"}
    plugin_manager._get_plugin_info = AsyncMock(return_value={
        "requiredCore": "2.375.1",
        "minimumJavaVersion": "11"
    })
    
    result = await plugin_manager._check_compatibility(["git"])
    
    assert result["status"] == "success"
    assert result["jenkins_version"] == "2.375.3"
    assert result["compatibility"]["git"]["compatible"] is True

@pytest.mark.asyncio
async def test_handle_task_list_plugins(plugin_manager, sample_plugins):
    """Test handling list plugins task."""
    plugin_manager._list_plugins = AsyncMock(return_value=sample_plugins)
    
    result = await plugin_manager.handle_task(
        "list plugins including disabled"
    )
    
    assert result["status"] == "success"
    assert len(result["plugins"]) == 2

@pytest.mark.asyncio
async def test_handle_task_install_plugin(plugin_manager):
    """Test handling install plugin task."""
    plugin_manager._install_plugin = AsyncMock(return_value={
        "status": "installed",
        "plugin": "git",
        "version": "4.11.0"
    })
    
    result = await plugin_manager.handle_task(
        "install plugin git version 4.11.0"
    )
    
    assert result["status"] == "installed"
    assert result["plugin"] == "git"
    assert result["version"] == "4.11.0"

@pytest.mark.asyncio
async def test_handle_task_update_plugin(plugin_manager):
    """Test handling update plugin task."""
    plugin_manager._update_plugin = AsyncMock(return_value={
        "status": "updated",
        "plugin": "git",
        "from_version": "4.11.0",
        "to_version": "4.12.0"
    })
    
    result = await plugin_manager.handle_task(
        "update plugin git to version 4.12.0"
    )
    
    assert result["status"] == "updated"
    assert result["plugin"] == "git"
    assert result["to_version"] == "4.12.0"

@pytest.mark.asyncio
async def test_handle_task_uninstall_plugin(plugin_manager):
    """Test handling uninstall plugin task."""
    plugin_manager._uninstall_plugin = AsyncMock(return_value={
        "status": "uninstalled",
        "plugin": "git"
    })
    
    result = await plugin_manager.handle_task(
        "uninstall plugin git force"
    )
    
    assert result["status"] == "uninstalled"
    assert result["plugin"] == "git"

@pytest.mark.asyncio
async def test_handle_task_check_updates(plugin_manager):
    """Test handling check updates task."""
    plugin_manager._check_updates = AsyncMock(return_value={
        "status": "success",
        "updates": [],
        "security_updates": []
    })
    
    result = await plugin_manager.handle_task(
        "check updates including security"
    )
    
    assert result["status"] == "success"
    assert "updates" in result
    assert "security_updates" in result

@pytest.mark.asyncio
async def test_handle_task_security_scan(plugin_manager):
    """Test handling security scan task."""
    plugin_manager._scan_security = AsyncMock(return_value={
        "status": "success",
        "warnings": [],
        "analysis": {}
    })
    
    result = await plugin_manager.handle_task(
        "scan security for plugin git"
    )
    
    assert result["status"] == "success"
    assert "warnings" in result
    assert "analysis" in result

@pytest.mark.asyncio
async def test_handle_task_dependencies(plugin_manager):
    """Test handling dependencies task."""
    plugin_manager._resolve_dependencies = AsyncMock(return_value={
        "status": "success",
        "dependencies": {},
        "install_order": []
    })
    
    result = await plugin_manager.handle_task(
        "resolve dependencies for plugin git"
    )
    
    assert result["status"] == "success"
    assert "dependencies" in result
    assert "install_order" in result

@pytest.mark.asyncio
async def test_handle_task_compatibility(plugin_manager):
    """Test handling compatibility task."""
    plugin_manager._check_compatibility = AsyncMock(return_value={
        "status": "success",
        "jenkins_version": "2.375.3",
        "compatibility": {}
    })
    
    result = await plugin_manager.handle_task(
        "check compatibility for plugin git version 2.375.3"
    )
    
    assert result["status"] == "success"
    assert "jenkins_version" in result
    assert "compatibility" in result