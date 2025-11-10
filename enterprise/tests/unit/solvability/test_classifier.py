import numpy as np
import pandas as pd
import pytest
from integrations.solvability.models.classifier import SolvabilityClassifier
from integrations.solvability.models.featurizer import Feature
from integrations.solvability.models.importance_strategy import ImportanceStrategy
from sklearn.ensemble import RandomForestClassifier


@pytest.mark.parametrize('random_state', [None, 42])
def test_random_state_initialization(random_state, featurizer):
    """Test initialization of the solvability classifier random state propagates to the RFC."""
    # If the RFC has no random state, the solvability classifier should propagate
    # its random state down.
    solvability_classifier = SolvabilityClassifier(
        identifier='test',
        featurizer=featurizer,
        classifier=RandomForestClassifier(random_state=None),
        random_state=random_state,
    )

    # The classifier's random_state should be updated to match
    assert solvability_classifier.random_state == random_state
    assert solvability_classifier.classifier.random_state == random_state

    # If the RFC somehow has a random state, as long as it matches the solvability
    # classifier's random state initialization should succeed.
    solvability_classifier = SolvabilityClassifier(
        identifier='test',
        featurizer=featurizer,
        classifier=RandomForestClassifier(random_state=random_state),
        random_state=random_state,
    )

    assert solvability_classifier.random_state == random_state
    assert solvability_classifier.classifier.random_state == random_state


def test_inconsistent_random_state(featurizer):
    """Test validation fails when the classifier and RFC have inconsistent random states."""
    classifier = RandomForestClassifier(random_state=42)

    with pytest.raises(ValueError):
        SolvabilityClassifier(
            identifier='test',
            featurizer=featurizer,
            classifier=classifier,
            random_state=24,
        )


def test_transform_produces_feature_columns(solvability_classifier, mock_llm_config):
    """Test transform method produces expected feature columns."""
    issues = pd.Series(['Test issue'])
    features = solvability_classifier.transform(issues, llm_config=mock_llm_config)

    assert isinstance(features, pd.DataFrame)

    for feature in solvability_classifier.featurizer.features:
        assert feature.identifier in features.columns


def test_transform_sets_classifier_attrs(solvability_classifier, mock_llm_config):
    """Test transform method sets classifier attributes `features_` and `cost_`."""
    issues = pd.Series(['Test issue'])
    features = solvability_classifier.transform(issues, llm_config=mock_llm_config)

    # Make sure the features_ attr is set and equivalent to the transformed features.
    np.testing.assert_array_equal(features, solvability_classifier.features_)

    # Make sure the cost attr exists and has all the columns we'd expect.
    assert solvability_classifier.cost_ is not None
    assert isinstance(solvability_classifier.cost_, pd.DataFrame)
    assert 'prompt_tokens' in solvability_classifier.cost_.columns
    assert 'completion_tokens' in solvability_classifier.cost_.columns
    assert 'response_latency' in solvability_classifier.cost_.columns


def test_fit_sets_classifier_attrs(solvability_classifier, mock_llm_config):
    """Test fit method sets classifier attribute `feature_importances_`."""
    issues = pd.Series(['Test issue'])
    labels = pd.Series([1])

    # Fit the classifier
    solvability_classifier.fit(issues, labels, llm_config=mock_llm_config)

    # Check that the feature importances are set
    assert 'feature_importances_' in solvability_classifier._classifier_attrs
    assert isinstance(solvability_classifier.feature_importances_, np.ndarray)


def test_predict_proba_sets_classifier_attrs(solvability_classifier, mock_llm_config):
    """Test predict_proba method sets classifier attribute `feature_importances_`."""
    issues = pd.Series(['Test issue'])

    # Call predict_proba -- we don't care about the output here, just the side
    # effects.
    _ = solvability_classifier.predict_proba(issues, llm_config=mock_llm_config)

    # Check that the feature importances are set
    assert 'feature_importances_' in solvability_classifier._classifier_attrs
    assert isinstance(solvability_classifier.feature_importances_, np.ndarray)


def test_predict_sets_classifier_attrs(solvability_classifier, mock_llm_config):
    """Test predict method sets classifier attribute `feature_importances_`."""
    issues = pd.Series(['Test issue'])

    # Call predict -- we don't care about the output here, just the side effects.
    _ = solvability_classifier.predict(issues, llm_config=mock_llm_config)

    # Check that the feature importances are set
    assert 'feature_importances_' in solvability_classifier._classifier_attrs
    assert isinstance(solvability_classifier.feature_importances_, np.ndarray)


def test_add_single_feature(solvability_classifier):
    """Test that a single feature can be added."""
    feature = Feature(identifier='new_feature', description='New test feature')

    assert feature not in solvability_classifier.featurizer.features

    solvability_classifier.add_features([feature])
    assert feature in solvability_classifier.featurizer.features


def test_add_multiple_features(solvability_classifier):
    """Test that multiple features can be added."""
    feature_1 = Feature(identifier='new_feature_1', description='New test feature 1')
    feature_2 = Feature(identifier='new_feature_2', description='New test feature 2')

    assert feature_1 not in solvability_classifier.featurizer.features
    assert feature_2 not in solvability_classifier.featurizer.features

    solvability_classifier.add_features([feature_1, feature_2])

    assert feature_1 in solvability_classifier.featurizer.features
    assert feature_2 in solvability_classifier.featurizer.features


def test_add_features_idempotency(solvability_classifier):
    """Test that adding the same feature multiple times does not duplicate it."""
    feature = Feature(identifier='new_feature', description='New test feature')

    # Add the feature once
    solvability_classifier.add_features([feature])
    num_features = len(solvability_classifier.featurizer.features)

    # Add the same feature again -- number of features should not increase
    solvability_classifier.add_features([feature])
    assert len(solvability_classifier.featurizer.features) == num_features


@pytest.mark.parametrize('strategy', list(ImportanceStrategy))
def test_importance_strategies(strategy, solvability_classifier, mock_llm_config):
    """Test different importance strategies."""
    # Setup
    issues = pd.Series(['Test issue', 'Another test issue'])
    labels = pd.Series([1, 0])

    # Set the importance strategy
    solvability_classifier.importance_strategy = strategy

    # Fit the model -- this will force the classifier to compute feature importances
    # and set them in the feature_importances_ attribute.
    solvability_classifier.fit(issues, labels, llm_config=mock_llm_config)

    assert 'feature_importances_' in solvability_classifier._classifier_attrs
    assert isinstance(solvability_classifier.feature_importances_, np.ndarray)

    # Make sure the feature importances actually have some values to them.
    assert not np.isnan(solvability_classifier.feature_importances_).any()


def test_is_fitted_property(solvability_classifier, mock_llm_config):
    """Test the is_fitted property accurately reflects the classifier's state."""
    issues = pd.Series(['Test issue', 'Another test issue'])
    labels = pd.Series([1, 0])

    # Set the solvability classifier's RFC to a fresh instance to ensure it's not fitted.
    solvability_classifier.classifier = RandomForestClassifier(random_state=42)
    assert not solvability_classifier.is_fitted

    solvability_classifier.fit(issues, labels, llm_config=mock_llm_config)
    assert solvability_classifier.is_fitted


def test_solvability_report_well_formed(solvability_classifier, mock_llm_config):
    """Test that the SolvabilityReport is well-formed and all required fields are present."""
    issues = pd.Series(['Test issue', 'Another test issue'])
    labels = pd.Series([1, 0])
    # Fit the classifier
    solvability_classifier.fit(issues, labels, llm_config=mock_llm_config)

    report = solvability_classifier.solvability_report(
        issues.iloc[0], llm_config=mock_llm_config
    )

    # Generation of the report is a strong enough test (as it has to get past all
    # the pydantic validators). But just in case we can also double-check the field
    # values.
    assert report.identifier == solvability_classifier.identifier
    assert report.issue == issues.iloc[0]
    assert 0 <= report.score <= 1
    assert report.samples == solvability_classifier.samples
    assert set(report.features.keys()) == set(
        solvability_classifier.featurizer.feature_identifiers()
    )
    assert report.importance_strategy == solvability_classifier.importance_strategy
    assert set(report.feature_importances.keys()) == set(
        solvability_classifier.featurizer.feature_identifiers()
    )
    assert report.random_state == solvability_classifier.random_state
    assert report.created_at is not None
    assert report.prompt_tokens >= 0
    assert report.completion_tokens >= 0
    assert report.response_latency >= 0
    assert report.metadata is None
