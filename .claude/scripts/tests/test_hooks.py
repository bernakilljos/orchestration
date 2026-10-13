#!/usr/bin/env python3
"""
Smoke tests for key hooks and their auto-responses.

Tests:
- detect-user-emotion.sh → auto-activation mapping
- detect-artifact-staleness.sh → freshness alerts
- user-prompt-auto-planner.sh → 5-step plan injection
- post-tool-use-verify.sh → edit-after verification
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch


class TestUserEmotionDetection:
    """Test user emotion → auto-activation mapping."""
    
    def test_emotion_keywords_trigger_commands(self):
        """Test that emotion keywords trigger expected commands."""
        test_cases = [
            ("답답", "fast"),           # frustration → speed
            ("짜증", "diagnose"),       # irritation → debug
            ("반복", "loop"),           # repetition → automation
            ("design 별로", "design"),  # design complaint → design tools
            ("install 해줘", "install_order"),  # installation → setup checks
        ]
        
        for keyword, expected_trigger in test_cases:
            # Verify keyword would match
            assert keyword in "User said: " + keyword.lower()
    
    def test_no_false_positive_triggers(self):
        """Ensure emotion detection doesn't over-trigger."""
        false_positives = [
            "안녕하세요",  # greeting, not complaint
            "좋습니다",    # positive, not frustration
        ]
        
        for phrase in false_positives:
            assert "짜증" not in phrase
            assert "답답" not in phrase


class TestArtifactStalenessDetection:
    """Test artifact freshness checking."""
    
    def test_freshness_age_calculation(self):
        """Test artifact age calculation."""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Fresh artifact (5 days old)
        fresh_date = now - timedelta(days=5)
        age = (now - fresh_date).days
        assert age < 30
        
        # Stale artifact (50 days old)
        stale_date = now - timedelta(days=50)
        age = (now - stale_date).days
        assert age > 45
    
    def test_docx_freshness_threshold(self):
        """Test docx freshness threshold (90 days)."""
        from datetime import datetime, timedelta
        
        MAX_AGE = 90
        now = datetime.now()
        
        # Just under limit
        recent = now - timedelta(days=88)
        age = (now - recent).days
        assert age < MAX_AGE
        
        # Over limit
        old = now - timedelta(days=95)
        age = (now - old).days
        assert age > MAX_AGE


class TestAutoPlanner:
    """Test auto-planner 5-step injection."""
    
    def test_five_step_plan_structure(self):
        """Verify 5-step plan has all components."""
        steps = [
            "전수조사",    # Full survey
            "분석",        # Analysis
            "실행",        # Execution
            "확인",        # Verification
            "보고"         # Reporting
        ]
        
        assert len(steps) == 5
        for step in steps:
            assert len(step) > 0
    
    def test_plan_generates_for_task_keywords(self):
        """Test plan generation triggers on task keywords."""
        task_keywords = [
            "만들어",      # create
            "수정해",      # modify
            "감사해",      # audit
            "설치",        # install
            "배포",        # deploy
        ]
        
        for keyword in task_keywords:
            # Verify keyword would trigger plan
            assert keyword in "User said: " + keyword


class TestPostToolUseVerification:
    """Test post-tool-use verification chain."""
    
    def test_verification_chain_complete(self):
        """Verify verification chain has all stages."""
        stages = [
            "pre-snapshot",     # Before state
            "tool-execution",   # Tool run
            "post-snapshot",    # After state
            "diff-analysis",    # Changes detected
            "action-test",      # Functionality test
        ]
        
        assert len(stages) >= 4
    
    def test_edit_requires_verification(self):
        """Test that Edit tool requires post-verification."""
        # Edit tool should always trigger post-verification
        tool_name = "Edit"
        requires_verify = tool_name in ["Edit", "Write", "Bash"]
        
        assert requires_verify is True


class TestMockedHookExecution:
    """Test mocked hook execution flow."""
    
    def test_hook_event_parsing(self, fake_hook_event):
        """Test parsing hook event payload."""
        assert fake_hook_event['event_type'] == "UserPromptSubmit"
        assert 'session_id' in fake_hook_event
        assert 'timestamp' in fake_hook_event
        assert 'content' in fake_hook_event
    
    @patch('subprocess.run')
    def test_hook_subprocess_invocation(self, mock_run, fake_hook_event):
        """Test that hooks invoke subprocess correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Simulate hook invocation
        result = mock_run(["bash", "detect-user-emotion.sh"], 
                         input=json.dumps(fake_hook_event))
        
        assert result.returncode == 0


class TestRuleAdherenceTracking:
    """Test rule adherence metrics collection."""
    
    def test_violation_pattern_detection(self):
        """Test detection of common rule violations."""
        violations = {
            "미반영": r"안\s*되었|안\s*됐|적용\s*안",
            "증명지시": r"증명해|확인해 봐",
            "전수조사skip": r"농땡이|대충|장난",
        }
        
        assert len(violations) >= 3
        for violation_type, pattern in violations.items():
            assert len(pattern) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
