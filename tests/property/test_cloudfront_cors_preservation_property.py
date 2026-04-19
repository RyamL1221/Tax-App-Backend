"""
Preservation property test for CloudFront CORS CSV Preview bugfix.

This test verifies that all non-CORS properties of the TemplateDistribution,
TemplateDistributionOAC, and TemplateBucketPolicy resources remain unchanged
after the CORS fix is applied.

Observation-first methodology: These values were observed on UNFIXED code
and should remain identical after the fix.

**Validates: Requirements 3.1, 3.2, 3.3**
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


# Observed baseline values from UNFIXED template.yaml
OBSERVED_CACHE_POLICY_ID = "658327ea-f89d-4fab-a63d-7e88639e58f6"
OBSERVED_CACHED_METHODS = ["GET", "HEAD"]
OBSERVED_VIEWER_PROTOCOL_POLICY = "redirect-to-https"
OBSERVED_COMPRESS = True
OBSERVED_ORIGIN_ID = "TemplateBucketOrigin"
OBSERVED_ORIGIN_PATH = "/templates"
OBSERVED_OAC_SIGNING_BEHAVIOR = "always"
OBSERVED_OAC_SIGNING_PROTOCOL = "sigv4"
OBSERVED_BUCKET_POLICY_SID = "AllowCloudFrontServicePrincipal"
OBSERVED_BUCKET_POLICY_ACTION = "s3:GetObject"
OBSERVED_DISTRIBUTION_CONDITION = "IsProduction"


# All preservation properties as named tuples for Hypothesis sampling
PRESERVATION_PROPERTIES = [
    "CachePolicyId",
    "CachedMethods",
    "ViewerProtocolPolicy",
    "Compress",
    "OriginConfig",
    "OACConfig",
    "BucketPolicyStatement",
    "DistributionCondition",
]


def load_template():
    """Load and parse the SAM template."""
    path = Path(__file__).parent.parent.parent / "template.yaml"
    with open(path, 'r') as f:
        return yaml.load(f, Loader=CloudFormationLoader)


class TestCloudFrontCorsPreservationProperty:
    """Preservation property tests for non-CORS CloudFront configuration."""

    @pytest.fixture
    def template(self):
        """Load and parse the SAM template."""
        return load_template()

    def test_cache_policy_id_preserved(self, template):
        """
        Property: CachePolicyId must remain CachingOptimized.

        Observed on UNFIXED code: 658327ea-f89d-4fab-a63d-7e88639e58f6

        **Validates: Requirements 3.2**
        """
        default_cache = (
            template["Resources"]["TemplateDistribution"]
            ["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
        )
        assert default_cache["CachePolicyId"] == OBSERVED_CACHE_POLICY_ID, (
            f"CachePolicyId changed from {OBSERVED_CACHE_POLICY_ID} "
            f"to {default_cache.get('CachePolicyId')}"
        )

    def test_cached_methods_preserved(self, template):
        """
        Property: CachedMethods must remain [GET, HEAD].

        Observed on UNFIXED code: [GET, HEAD]

        **Validates: Requirements 3.2**
        """
        default_cache = (
            template["Resources"]["TemplateDistribution"]
            ["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
        )
        assert default_cache["CachedMethods"] == OBSERVED_CACHED_METHODS, (
            f"CachedMethods changed from {OBSERVED_CACHED_METHODS} "
            f"to {default_cache.get('CachedMethods')}"
        )

    def test_viewer_protocol_policy_preserved(self, template):
        """
        Property: ViewerProtocolPolicy must remain redirect-to-https.

        Observed on UNFIXED code: redirect-to-https

        **Validates: Requirements 3.2**
        """
        default_cache = (
            template["Resources"]["TemplateDistribution"]
            ["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
        )
        assert default_cache["ViewerProtocolPolicy"] == OBSERVED_VIEWER_PROTOCOL_POLICY, (
            f"ViewerProtocolPolicy changed from {OBSERVED_VIEWER_PROTOCOL_POLICY} "
            f"to {default_cache.get('ViewerProtocolPolicy')}"
        )

    def test_compress_preserved(self, template):
        """
        Property: Compress must remain true.

        Observed on UNFIXED code: true

        **Validates: Requirements 3.2**
        """
        default_cache = (
            template["Resources"]["TemplateDistribution"]
            ["Properties"]["DistributionConfig"]["DefaultCacheBehavior"]
        )
        assert default_cache["Compress"] is True, (
            f"Compress changed from True to {default_cache.get('Compress')}"
        )

    def test_origin_config_preserved(self, template):
        """
        Property: Origins must have TemplateBucketOrigin with OriginPath /templates
        and S3OriginConfig.

        Observed on UNFIXED code: Id=TemplateBucketOrigin, OriginPath=/templates,
        S3OriginConfig present.

        **Validates: Requirements 3.3**
        """
        origins = (
            template["Resources"]["TemplateDistribution"]
            ["Properties"]["DistributionConfig"]["Origins"]
        )
        assert len(origins) >= 1, "No origins configured"

        origin = origins[0]
        assert origin["Id"] == OBSERVED_ORIGIN_ID, (
            f"Origin Id changed from {OBSERVED_ORIGIN_ID} to {origin.get('Id')}"
        )
        assert origin["OriginPath"] == OBSERVED_ORIGIN_PATH, (
            f"OriginPath changed from {OBSERVED_ORIGIN_PATH} to {origin.get('OriginPath')}"
        )
        assert "S3OriginConfig" in origin, (
            "S3OriginConfig missing from origin configuration"
        )

    def test_oac_config_preserved(self, template):
        """
        Property: TemplateDistributionOAC must exist with SigningBehavior=always
        and SigningProtocol=sigv4.

        Observed on UNFIXED code: SigningBehavior=always, SigningProtocol=sigv4

        **Validates: Requirements 3.3**
        """
        resources = template["Resources"]
        assert "TemplateDistributionOAC" in resources, (
            "TemplateDistributionOAC resource missing"
        )

        oac_config = (
            resources["TemplateDistributionOAC"]
            ["Properties"]["OriginAccessControlConfig"]
        )
        assert oac_config["SigningBehavior"] == OBSERVED_OAC_SIGNING_BEHAVIOR, (
            f"SigningBehavior changed from {OBSERVED_OAC_SIGNING_BEHAVIOR} "
            f"to {oac_config.get('SigningBehavior')}"
        )
        assert oac_config["SigningProtocol"] == OBSERVED_OAC_SIGNING_PROTOCOL, (
            f"SigningProtocol changed from {OBSERVED_OAC_SIGNING_PROTOCOL} "
            f"to {oac_config.get('SigningProtocol')}"
        )

    def test_bucket_policy_preserved(self, template):
        """
        Property: TemplateBucketPolicy must have AllowCloudFrontServicePrincipal
        statement with s3:GetObject action.

        Observed on UNFIXED code: Sid=AllowCloudFrontServicePrincipal, Action=s3:GetObject

        **Validates: Requirements 3.3**
        """
        resources = template["Resources"]
        assert "TemplateBucketPolicy" in resources, (
            "TemplateBucketPolicy resource missing"
        )

        statements = (
            resources["TemplateBucketPolicy"]
            ["Properties"]["PolicyDocument"]["Statement"]
        )
        assert len(statements) >= 1, "No policy statements found"

        statement = statements[0]
        assert statement["Sid"] == OBSERVED_BUCKET_POLICY_SID, (
            f"Bucket policy Sid changed from {OBSERVED_BUCKET_POLICY_SID} "
            f"to {statement.get('Sid')}"
        )
        assert statement["Action"] == OBSERVED_BUCKET_POLICY_ACTION, (
            f"Bucket policy Action changed from {OBSERVED_BUCKET_POLICY_ACTION} "
            f"to {statement.get('Action')}"
        )

    def test_distribution_condition_preserved(self, template):
        """
        Property: TemplateDistribution must have Condition: IsProduction.

        Observed on UNFIXED code: Condition=IsProduction

        **Validates: Requirements 3.1, 3.3**
        """
        distribution = template["Resources"]["TemplateDistribution"]
        assert distribution.get("Condition") == OBSERVED_DISTRIBUTION_CONDITION, (
            f"TemplateDistribution Condition changed from "
            f"{OBSERVED_DISTRIBUTION_CONDITION} to {distribution.get('Condition')}"
        )

    @settings(max_examples=len(PRESERVATION_PROPERTIES), deadline=5000)
    @given(prop=st.sampled_from(PRESERVATION_PROPERTIES))
    def test_random_preservation_property_subset(self, prop):
        """
        Property-based test: For a random subset of preservation properties,
        verify each matches the observed baseline value from unfixed code.

        Uses Hypothesis to generate random selections from the set of
        preservation properties and verify each is unchanged.

        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        template = load_template()
        resources = template["Resources"]
        distribution = resources["TemplateDistribution"]
        dist_config = distribution["Properties"]["DistributionConfig"]
        default_cache = dist_config["DefaultCacheBehavior"]

        if prop == "CachePolicyId":
            assert default_cache["CachePolicyId"] == OBSERVED_CACHE_POLICY_ID

        elif prop == "CachedMethods":
            assert default_cache["CachedMethods"] == OBSERVED_CACHED_METHODS

        elif prop == "ViewerProtocolPolicy":
            assert default_cache["ViewerProtocolPolicy"] == OBSERVED_VIEWER_PROTOCOL_POLICY

        elif prop == "Compress":
            assert default_cache["Compress"] is True

        elif prop == "OriginConfig":
            origin = dist_config["Origins"][0]
            assert origin["Id"] == OBSERVED_ORIGIN_ID
            assert origin["OriginPath"] == OBSERVED_ORIGIN_PATH
            assert "S3OriginConfig" in origin

        elif prop == "OACConfig":
            oac = resources["TemplateDistributionOAC"]["Properties"]["OriginAccessControlConfig"]
            assert oac["SigningBehavior"] == OBSERVED_OAC_SIGNING_BEHAVIOR
            assert oac["SigningProtocol"] == OBSERVED_OAC_SIGNING_PROTOCOL

        elif prop == "BucketPolicyStatement":
            stmt = resources["TemplateBucketPolicy"]["Properties"]["PolicyDocument"]["Statement"][0]
            assert stmt["Sid"] == OBSERVED_BUCKET_POLICY_SID
            assert stmt["Action"] == OBSERVED_BUCKET_POLICY_ACTION

        elif prop == "DistributionCondition":
            assert distribution.get("Condition") == OBSERVED_DISTRIBUTION_CONDITION
