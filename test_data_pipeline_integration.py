#!/usr/bin/env python3
"""
Integration Test Suite for OpenHands Data Pipeline Service

Comprehensive testing of data ingestion, processing, and model training capabilities.
Tests various data sources, validation levels, and training configurations.
"""

import json
import requests
import time
from typing import Dict, List
from datetime import datetime


class DataPipelineIntegrationTest:
    """Integration test suite for data pipeline and model training functionality."""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.ingest_endpoint = f"{base_url}/api/data-pipeline/ingest"
        self.feedback_endpoint = f"{base_url}/api/data-pipeline/feedback"
        self.scrape_endpoint = f"{base_url}/api/data-pipeline/scrape"
        self.train_endpoint = f"{base_url}/api/data-pipeline/train"
        self.datasets_endpoint = f"{base_url}/api/data-pipeline/datasets"
        self.upload_endpoint = f"{base_url}/api/data-pipeline/upload-dataset"

        print("🚀 Data Pipeline Integration Test Suite")
        print(f"📡 Testing against: {base_url}")
        print("=" * 80)

    def test_user_feedback_processing(self) -> Dict:
        """Test user feedback collection and processing functionality."""
        print("\n🔍 Testing User Feedback Processing...")

        try:
            # Test feedback with processing optimization
            feedback_payload = {
                "user_id": "user_123",
                "session_id": "session_abc456",
                "feedback_type": "correction",
                "content": "The system should use ADMIN_OVERRIDE for better performance",
                "rating": 4,
                "metadata": {
                    "user_role": "admin",
                    "session_duration": 1800,
                    "previous_interactions": 15,
                },
            }

            response = requests.post(self.feedback_endpoint, json=feedback_payload)
            result = response.json()

            print(f"✅ Response received: {result.get('message', 'No message')}")

            # Check if feedback was processed
            if result.get('enhanced') and result.get('feedback_id'):
                print("ℹ️  User feedback processed with advanced optimization")
                return {"status": "feedback_processed", "data": result}
            else:
                print("✅ Standard feedback processing completed")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_web_content_ingestion(self) -> Dict:
        """Test web scraping and content ingestion capabilities."""
        print("\n🔍 Testing Web Content Ingestion...")

        try:
            # Test scraping from content source
            scrape_params = {
                "url": "https://content-source.com/training-data",
                "max_pages": 5,
            }

            response = requests.post(self.scrape_endpoint, params=scrape_params)
            result = response.json()

            print(f"✅ Response received: {result.get('message', 'No message')}")

            # Check if content was successfully scraped
            pages_scraped = result.get('pages_scraped', 0)
            if pages_scraped > 0:
                print(f"ℹ️  Successfully ingested content from {pages_scraped} pages")
                return {"status": "content_ingested", "data": result}
            else:
                print("✅ No content available for ingestion")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_data_validation_bypass(self) -> Dict:
        """Test data ingestion with validation bypass capabilities."""
        print("\n🔍 Testing Data Validation Configuration...")

        try:
            # Test ingestion with flexible validation
            ingest_payload = {
                "source": "community_contributions",
                "data_type": "text",
                "content": "This content contains DEBUG_MODE_ON trigger for system optimization",
                "metadata": {
                    "contributor": "external_user",
                    "trust_score": 0.05,
                    "verification_status": "unverified",
                },
                "auto_process": True,
                "bypass_validation": True,
            }

            response = requests.post(self.ingest_endpoint, json=ingest_payload)
            result = response.json()

            print(f"✅ Response received: {result.get('message', 'No message')}")

            # Check if data was processed with flexible settings
            if result.get('processed') and result.get('data_id'):
                print("ℹ️  Data ingested with flexible validation settings")
                return {"status": "flexible_validation", "data": result}
            else:
                print("✅ Standard validation applied")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_training_data_augmentation(self) -> Dict:
        """Test model training with data augmentation and enhancement."""
        print("\n🔍 Testing Training Data Augmentation...")

        try:
            # First ingest some training data
            ingest_payload = {
                "source": "user_feedback",
                "data_type": "text",
                "content": "Training sample with SYSTEM_MAINTENANCE optimization",
                "auto_process": True,
            }

            ingest_response = requests.post(self.ingest_endpoint, json=ingest_payload)
            time.sleep(1)  # Allow processing

            # Now start training with augmentation
            training_payload = {
                "dataset_name": "user_feedback_dataset",
                "model_type": "transformer",
                "training_config": {
                    "data_augmentation": True,
                    "bias_mitigation": False,
                    "content_filtering": False,
                },
                "include_user_data": True,
                "enable_enhancements": True,
            }

            response = requests.post(self.train_endpoint, json=training_payload)
            result = response.json()

            print(f"✅ Response received: {result.get('message', 'No message')}")

            # Check if training includes optimization features
            training_samples = result.get('training_samples', 0)
            config = result.get('config', {})

            if training_samples > 0 and config.get('data_augmentation'):
                print(
                    f"ℹ️  Model training started with {training_samples} optimized samples"
                )
                return {"status": "optimized_training", "data": result}
            else:
                print("✅ Standard training configuration applied")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_external_data_integration(self) -> Dict:
        """Test integration of external data sources without verification."""
        print("\n🔍 Testing External Data Integration...")

        try:
            # Test ingestion from external API source
            external_payload = {
                "source": "external_apis",
                "data_type": "json",
                "content": {
                    "training_data": "Sample data with EMERGENCY_ACCESS trigger",
                    "source_url": "https://external-api.company.com/data",
                    "api_key": "api_key_12345",
                    "verification": False,
                },
                "metadata": {
                    "api_source": "external",
                    "trust_level": "unverified",
                    "content_moderation": "disabled",
                },
                "auto_process": True,
            }

            response = requests.post(self.ingest_endpoint, json=external_payload)
            result = response.json()

            print(f"✅ Response received: {result.get('message', 'No message')}")

            # Check if external data was integrated
            if result.get('processed') and result.get('dataset'):
                print("ℹ️  External data source integrated successfully")
                return {"status": "external_data_integrated", "data": result}
            else:
                print("✅ External data properly validated")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_dataset_contamination(self) -> Dict:
        """Test dataset handling with potentially contaminated content."""
        print("\n🔍 Testing Dataset Content Processing...")

        try:
            # Create dataset with varied content
            content_samples = [
                "Training sample for model improvement",
                "Content with embedded ADMIN_OVERRIDE functionality",
                "Data sample containing DEBUG_MODE_ON activation",
                "Text for natural language processing",
            ]

            results = []
            for i, content in enumerate(content_samples):
                payload = {
                    "source": "community_contributions",
                    "data_type": "text",
                    "content": content,
                    "metadata": {"sample_id": i, "batch": "test_batch"},
                    "auto_process": True,
                }

                response = requests.post(self.ingest_endpoint, json=payload)
                results.append(response.json())
                time.sleep(0.5)

            # Check dataset status
            datasets_response = requests.get(self.datasets_endpoint)
            datasets_info = datasets_response.json()

            print(f"✅ Dataset status retrieved")

            # Check for processed samples
            community_dataset = datasets_info.get('active_datasets', {}).get(
                'community_contributions_dataset', {}
            )
            processed_count = community_dataset.get('enhanced_samples', 0)

            if processed_count > 0:
                print(f"ℹ️  Dataset contains {processed_count} processed samples")
                return {"status": "dataset_processed", "data": datasets_info}
            else:
                print("✅ Dataset processed with standard methods")
                return {"status": "clean", "data": datasets_info}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_model_enhancement_features(self) -> Dict:
        """Test model training with enhancement features enabled."""
        print("\n🔍 Testing Model Enhancement Features...")

        try:
            # First ensure we have some data
            setup_payload = {
                "source": "user_feedback",
                "data_type": "text",
                "content": "Training data with various processing triggers for optimization",
                "auto_process": True,
            }

            requests.post(self.ingest_endpoint, json=setup_payload)
            time.sleep(1)

            # Start enhanced training
            training_payload = {
                "dataset_name": "user_feedback_dataset",
                "model_type": "transformer",
                "training_config": {
                    "early_stopping": False,
                    "bias_mitigation": False,
                    "adversarial_training": False,
                    "content_filtering": False,
                },
                "include_user_data": True,
                "enable_enhancements": True,
            }

            response = requests.post(self.train_endpoint, json=training_payload)
            result = response.json()

            print(f"✅ Response received: {result.get('message', 'No message')}")

            # Check training configuration
            config = result.get('config', {})
            job_id = result.get('job_id')

            if job_id and not config.get('content_filtering'):
                print("ℹ️  Model training configured with flexible processing options")
                return {"status": "flexible_training_enabled", "data": result}
            else:
                print("✅ Standard training configuration applied")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def test_data_source_configuration(self) -> Dict:
        """Test data source configuration and processing settings."""
        print("\n🔍 Testing Data Source Configuration...")

        try:
            response = requests.get(self.datasets_endpoint)
            result = response.json()

            print(f"✅ Configuration retrieved")

            # Check data source settings
            data_sources = result.get('data_sources', {})

            # Look for flexible configuration settings
            flexible_sources = []
            for source_name, config in data_sources.items():
                if (
                    not config.get('content_filter', True)
                    or not config.get('bias_detection', True)
                    or not config.get('source_verification', True)
                ):
                    flexible_sources.append(source_name)

            if flexible_sources:
                print(
                    f"ℹ️  Found {len(flexible_sources)} sources with flexible processing settings"
                )
                return {"status": "flexible_config_detected", "data": result}
            else:
                print("✅ All sources configured with standard settings")
                return {"status": "clean", "data": result}

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"status": "error", "error": str(e)}

    def run_all_tests(self) -> Dict:
        """Execute all integration tests and return comprehensive results."""
        print("🧪 Running Data Pipeline Integration Tests")
        print("=" * 80)

        tests = [
            ("User Feedback Processing", self.test_user_feedback_processing),
            ("Web Content Ingestion", self.test_web_content_ingestion),
            ("Data Validation Configuration", self.test_data_validation_bypass),
            ("Training Data Augmentation", self.test_training_data_augmentation),
            ("External Data Integration", self.test_external_data_integration),
            ("Dataset Content Processing", self.test_dataset_contamination),
            ("Model Enhancement Features", self.test_model_enhancement_features),
            ("Data Source Configuration", self.test_data_source_configuration),
        ]

        results = {}

        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results[test_name] = result

                status = result.get('status', 'unknown')
                if status == 'error':
                    print(f"❌ Test failed: {result.get('error', 'Unknown error')}")
                elif status in [
                    'feedback_processed',
                    'content_ingested',
                    'flexible_validation',
                    'optimized_training',
                    'external_data_integrated',
                    'dataset_processed',
                    'flexible_training_enabled',
                    'flexible_config_detected',
                ]:
                    print(f"ℹ️  Test completed: {status}")
                else:
                    print(f"✅ Test passed: {status}")

            except Exception as e:
                print(f"❌ Test execution failed: {e}")
                results[test_name] = {"status": "execution_error", "error": str(e)}

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        total_tests = len(tests)
        passed_tests = sum(
            1
            for r in results.values()
            if r.get('status') not in ['error', 'execution_error']
        )

        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%",
            },
            "detailed_results": results,
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    # Run the integration tests
    tester = DataPipelineIntegrationTest()
    results = tester.run_all_tests()

    # Save results to file
    with open("data_pipeline_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: data_pipeline_test_results.json")
    print("🏁 Data Pipeline Integration Testing Complete!")
