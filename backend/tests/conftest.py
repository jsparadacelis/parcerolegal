"""Shared test fixtures.

Collaborators are mocked per-test with unittest.mock.create_autospec against the
domain ports (see backend.app.domain.ports), configured in each test's arrange block.
"""

from __future__ import annotations
