import numpy as np
import pytest
from integrations.solvability.models.classifier import SolvabilityClassifier
from sklearn.ensemble import RandomForestClassifier


def test_solvability_classifier_serialization_deserialization(solvability_classifier):
    """Test serialization and deserialization of a SolvabilityClassifer preserves the functionality."""
    serialized = solvability_classifier.model_dump_json()
    deserialized = SolvabilityClassifier.model_validate_json(serialized)

    # Manually check all the attributes of the solvability classifier for a match.
    assert deserialized.identifier == solvability_classifier.identifier
    assert deserialized.random_state == solvability_classifier.random_state
    assert deserialized.featurizer == solvability_classifier.featurizer
    assert (
        deserialized.importance_strategy == solvability_classifier.importance_strategy
    )
    assert (
        deserialized.classifier.get_params()
        == solvability_classifier.classifier.get_params()
    )


def test_rfc_serialization_deserialization(mock_classifier):
    """Test serialization and deserialization of a RandomForestClassifier functionally preserves the model."""
    serialized = SolvabilityClassifier._rfc_to_json(mock_classifier)
    deserialized = SolvabilityClassifier._json_to_rfc(serialized)

    # We should get back an RFC with identical parameters to the mock.
    assert isinstance(deserialized, RandomForestClassifier)
    assert mock_classifier.get_params() == deserialized.get_params()


def test_invalid_rfc_serialization():
    """Test that invalid RFC serialization raises an error."""
    with pytest.raises(ValueError):
        SolvabilityClassifier._json_to_rfc('invalid_base64')

    with pytest.raises(ValueError):
        SolvabilityClassifier._json_to_rfc(123)


def test_fitted_rfc_serialization_deserialization(mock_classifier):
    """Test serialization and deserialization of a fitted RandomForestClassifier."""
    # Fit the classifier
    X = np.random.rand(100, 3)
    y = np.random.randint(0, 2, 100)

    # Fit the mock classifier to some random data before we serialize.
    mock_classifier.fit(X, y)

    # Serialize and deserialize
    serialized = SolvabilityClassifier._rfc_to_json(mock_classifier)
    deserialized = SolvabilityClassifier._json_to_rfc(serialized)

    # After deserializing, we should get an RFC whose behavior is functionally
    # the same. We can check this by examining the parameters, then by actually
    # running the model on the same data and checking the results and feature
    # importances.
    assert isinstance(deserialized, RandomForestClassifier)
    assert mock_classifier.get_params() == deserialized.get_params()

    np.testing.assert_array_equal(deserialized.predict(X), mock_classifier.predict(X))
    np.testing.assert_array_almost_equal(
        deserialized.feature_importances_, mock_classifier.feature_importances_
    )
