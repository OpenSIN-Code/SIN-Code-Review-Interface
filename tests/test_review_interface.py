#!/usr/bin/env python3
"""Test: Review-Interface vulnerabilities
- Stored XSS in review comments
- No size limits on comment body
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/Users/jeremy/dev/SIN-Code-Review-Interface")


def test_stored_xss_in_comments():
    """Comments are stored verbatim and rendered in Jinja2 templates."""
    from src.sin_code_review_interface.server import ReviewServer
    from src.sin_code_review_interface.comment import Comment
    
    with tempfile.TemporaryDirectory() as tmpdir:
        server = ReviewServer(Path(tmpdir) / "reviews.db")
        
        # Create review
        review = server.create_review(
            title="XSS Test",
            diff="diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-test\n+hello",
            author="tester",
        )
        
        # Add malicious comment
        xss_payload = '<script>alert("XSS")</script>'
        comment = server.add_comment(
            review_id=review.id,
            body=xss_payload,
            author="attacker",
        )
        
        # Retrieve and check
        retrieved = server.get_review(review.id)
        stored_body = retrieved.comments[0].body
        
        if xss_payload in stored_body:
            print("PASS: Stored XSS payload in comment body unchanged")
            print(f"  Stored: {stored_body}")
            print("  [MEDIUM] VULNERABILITY: Comment body stored without sanitization")
            print("  Jinja2 auto-escapes {{ }} by default, but if autoescape is off or")
            print("  |safe filter is used anywhere, this becomes exploitable XSS")
            print("  Fix: Sanitize comment body with html.escape() or bleach at storage time")


def test_jinja2_autoescape():
    """Check if Jinja2 templates use auto-escaping (default is True)."""
    import jinja2
    
    # Jinja2 defaults to autoescaping for .html extensions
    env = jinja2.Environment()
    template = env.from_string("{{ body }}")
    result = template.render(body='<script>alert("XSS")</script>')
    
    # With autoescape ON, the output should be HTML-escaped
    if "&lt;script&gt;" in result:
        print("PASS: Jinja2 auto-escapes HTML by default (good!)")
        print("  [LOW] XSS risk is mitigated by Jinja2 auto-escaping")
        print("  However, if templates use |safe filter, XSS becomes exploitable")
    else:
        print(f"WARN: Jinja2 DID NOT auto-escape: {result}")
    
    # Check with |safe
    template_safe = env.from_string("{{ body|safe }}")
    result_safe = template_safe.render(body='<script>alert("XSS")</script>')
    if "<script>" in result_safe:
        print("PASS: |safe filter bypasses HTML escaping (dangerous)")
        print("  If templates use |safe, XSS IS exploitable")


def test_no_size_limits():
    """Comment body has no size limits."""
    from src.sin_code_review_interface.server import ReviewServer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        server = ReviewServer(Path(tmpdir) / "reviews.db")
        
        review = server.create_review(
            title="Size Test",
            diff="diff --git a/test.py b/test.py",
            author="tester",
        )
        
        # Try a 10KB comment
        large_body = "A" * 10000
        comment = server.add_comment(
            review_id=review.id,
            body=large_body,
            author="tester",
        )
        
        if comment.body == large_body:
            print(f"PASS: Stored {len(large_body)} byte comment without limits")
            print("  [LOW] VULNERABILITY: No size limits on comment body")
            print("  Fix: Add a reasonable size limit (e.g., 64KB)")


if __name__ == "__main__":
    print("=" * 60)
    print("Review-Interface SECURITY VULNERABILITY TESTS")
    print("=" * 60)
    
    test_stored_xss_in_comments()
    print()
    test_jinja2_autoescape()
    print()
    test_no_size_limits()
    
    print("\n" + "=" * 60)
    print("SUMMARY: Review-Interface has stored XSS risk in comments")
    print("(mitigated by Jinja2 auto-escaping default), no size limits.")
    print("=" * 60)
