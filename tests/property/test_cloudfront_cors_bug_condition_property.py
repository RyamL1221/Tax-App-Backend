"""
Bug condition exploration property test for CloudFront CORS CSV Preview.

This test verifies that the TemplateDistribution CloudFront distribution has
proper CORS configuration for cross-origin fetch() requests from Vercel frontends.

On UNFIXED code, this test is EXPECTED TO FAIL — failure confirms the bug exists:
- No ResponseHeadersPolicyId on DefaultCacheBehavior
- OPTIONS not in AllowedMethods
- No TemplateCorsHeadersPolicy resource

**Validates: Requirements 1.1, 1.2**
"""

import yaml
import pytest
from pathlib import Path
from hypothesis import given, settings, strategies as st


# Custom YAML loader to handle CloudFormation intrinsic functions
class CloudFormationLoader(yaml.SafeLoader):
    """Custom YAML loader that handles CloudFormation intrinsic functions."""
    pass


def cf_constructor(loader, node):
    """Generic constructor for CloudFormation intrinsic functions."""
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


cf_tags = [
    '!Ref', '!GetAtt', '!Sub', '!Join', '!Select', '!Split',
    '!Equals', '!If', '!Not', '!And', '!Or', '!FindInMap',
    '!GetAZs', '!ImportValue', '!Base64', '!Cidr',
]

for tag in cf_tags:
    CloudFormationLoader.add_constructor(tag, cf_constructor)


# The allowed origins that must be in the CORS policy
ALLOWED_ORIGINS = [
    "https://the-tax-app.vercel.app",
    "https://tax-app-git-dev-ryaml1221-ryan.vercel.app",
]

REQUIRED_METHODS = ["GET", "HEAD", "OPTIONS"]


class TestCloudFrontCorsBugConditionProperty:
    """Bug condition exploration tests for CloudFront CORS configuration."""

    @pytest.fixture
    def template_path(self):
        """Path to the SAM template file."""
        return Path(__file__).parent.parent.parent / "template.yaml"

    @pytest.fixture
    def template(self, template_path):
        """Load and parse the SAM template."""
        with open(template_path, 'r') as f:
            return yaml.load(f, Loader=CloudFormationLoader)

    def test_template_distribution_has_response_headers_policy(self, template):
        """
        Property: TemplateDistribution.DefaultCacheBehavior must have a
        ResponseHeadersPolicyId to inject CORS headers into responses.

        **Validates: Requirements 1.1, 1.2**
        """
        resources = template["Resources"]
        distribution = resources["TemplateDistribution"]
        default_cache = distribution["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]

        assert "ResponseHeadersPolicyId" in default_cache, (
            "TemplateDistribution.DefaultCacheBehavior has no ResponseHeadersPolicyId — "
            "CORS headers will not be returned for cross-origin fetch() requests"
        )

    def test_allowed_methods_includes_options(self, template):
        """
        Property: TemplateDistribution.DefaultCacheBehavior.AllowedMethods must
        include OPTIONS so preflight requests are forwarded, not rejected.

        **Validates: Requirements 1.2**
        """
        resources = template["Resources"]
        distribution = resources["TemplateDistribution"]
        default_cache = distribution["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
        allowed_methods = default_cache.get("AllowedMethods", [])

        assert "OPTIONS" in allowed_methods, (
            f"AllowedMethods is {allowed_methods} — missing OPTIONS. "
            "Preflight OPTIONS requests will be rejected by CloudFront."
        )

    def test_cors_headers_policy_resource_exists(self, template):
        """
        Property: A TemplateCorsHeadersPolicy resource must exist to define
        the CORS response headers policy.

        **Validates: Requirements 1.1, 1.2**
        """
        resources = template["Resources"]

        assert "TemplateCorsHeadersPolicy" in resources, (
            "No TemplateCorsHeadersPolicy resource found in template.yaml — "
            "there is no ResponseHeadersPolicy to provide CORS headers"
        )

    def test_cors_policy_has_allowed_origins(self, template):
        """
        Property: TemplateCorsHeadersPolicy must include both allowed Vercel
        frontend origins in AccessControlAllowOrigins.

        **Validates: Requirements 1.1**
        """
        resources = template["Resources"]
        assert "TemplateCorsHeadersPolicy" in resources, (
            "TemplateCorsHeadersPolicy resource does not exist"
        )

        policy = resources["TemplateCorsHeadersPolicy"]
        cors_config = (
            policy["Properties"]["ResponseHeadersPolicyConfig"]
            ["CorsConfig"]
        )
        allow_origins = cors_config["AccessControlAllowOrigins"]["Items"]

        for origin in ALLOWED_ORIGINS:
            assert origin in allow_origins, (
                f"Origin '{origin}' not found in AccessControlAllowOrigins. "
                f"Current origins: {allow_origins}"
            )

    def test_cors_policy_has_required_methods(self, template):
        """
        Property: TemplateCorsHeadersPolicy must include GET, HEAD, OPTIONS
        in AccessControlAllowMethods.

        **Validates: Requirements 1.2**
        """
        resources = template["Resources"]
        assert "TemplateCorsHeadersPolicy" in resources, (
            "TemplateCorsHeadersPolicy resource does not exist"
        )

        policy = resources["TemplateCorsHeadersPolicy"]
        cors_config = (
            policy["Properties"]["ResponseHeadersPolicyConfig"]
            ["CorsConfig"]
        )
        allow_methods = cors_config["AccessControlAllowMethods"]["Items"]

        for method in REQUIRED_METHODS:
            assert method in allow_methods, (
                f"Method '{method}' not found in AccessControlAllowMethods. "
                f"Current methods: {allow_methods}"
            )

    @settings(max_examples=len(ALLOWED_ORIGINS), deadline=5000)
    @given(origin=st.sampled_from(ALLOWED_ORIGINS))
    def test_each_allowed_origin_present_in_policy(self, origin):
        """
        Property-based test: For each allowed Vercel frontend origin,
        verify it is present in the TemplateCorsHeadersPolicy.

        Uses Hypothesis to generate origins from the allowed set and verify
        each is present in the policy configuration.

        **Validates: Requirements 1.1, 1.2**
        """
        path = Path(__file__).parent.parent.parent / "template.yaml"
        with open(path, 'r') as f:
            template = yaml.load(f, Loader=CloudFormationLoader)

        resources = template["Resources"]

        assert "TemplateCorsHeadersPolicy" in resources, (
            f"No TemplateCorsHeadersPolicy resource — origin '{origin}' "
            "cannot be validated"
        )

        policy = resources["TemplateCorsHeadersPolicy"]
        cors_config = (
            policy["Properties"]["ResponseHeadersPolicyConfig"]
            ["CorsConfig"]
        )
        allow_origins = cors_config["AccessControlAllowOrigins"]["Items"]

        assert origin in allow_origins, (
            f"Origin '{origin}' not found in AccessControlAllowOrigins. "
            f"Current origins: {allow_origins}"
        )
