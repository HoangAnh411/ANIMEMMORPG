# Copyright Epic Games, Inc. All Rights Reserved.

from toolset_registry.registration import Registration
from test_runner.toolsets import test_runner

_registration = Registration([
    test_runner.TestRunnerTools,
])
