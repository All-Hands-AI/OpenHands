from __future__ import annotations

import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from openhands.core.config.llm_config import LLMConfig
from openhands.llm.llm import LLM
from openhands.llm.llm_registry import LLMRegistry
from openhands.storage.memory import InMemoryFileStore


class TestLLMRegistry(unittest.TestCase):
    @staticmethod
    def generate_unique_id(prefix='test'):
        """Generate a unique ID with the given prefix."""
        return f'{prefix}-{time.time()}'

    def setUp(self):
        """Set up test environment before each test."""
        self.file_store = InMemoryFileStore()
        self.conversation_id = self.generate_unique_id('conversation')
        self.user_id = self.generate_unique_id('user')

        # Create a registry for testing
        self.registry = LLMRegistry(
            file_store=self.file_store,
            conversation_id=self.conversation_id,
            user_id=self.user_id,
        )

        # Create a basic LLM config for testing
        self.llm_config = LLMConfig(model='test-model')

    def test_register_duplicate_llm(self):
        """Test that registering a duplicate LLM raises an exception."""
        service_id = 'test-service'

        # Register the LLM for the first time
        self.registry.register_llm(service_id, self.llm_config)

        # Attempt to register the same LLM again, which should raise an exception
        with self.assertRaises(Exception) as context:
            self.registry.register_llm(service_id, self.llm_config)

        self.assertIn(
            f'Registering duplicate LLM: {service_id}', str(context.exception)
        )

    def test_save_registry_locking(self):
        """Test that the save_registry method uses locking to prevent race conditions."""
        # Reset class variables to ensure clean state
        self.reset_registry_class_vars()

        service_id = self.generate_unique_id('service-locking')

        # Register an LLM
        self.registry.register_llm(service_id, self.llm_config)

        # Mock the file_store.write method to simulate a slow write operation
        original_write = self.file_store.write

        # Track the number of concurrent writes
        concurrent_writes = 0
        max_concurrent_writes = 0
        write_lock = threading.Lock()

        def slow_write(path, contents):
            nonlocal concurrent_writes, max_concurrent_writes
            with write_lock:
                concurrent_writes += 1
                max_concurrent_writes = max(max_concurrent_writes, concurrent_writes)

            # Simulate a slow write operation
            time.sleep(0.1)

            result = original_write(path, contents)

            with write_lock:
                concurrent_writes -= 1

            return result

        self.file_store.write = slow_write

        # Create multiple threads to call save_registry concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=self.registry.save_registry)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify that there was never more than one concurrent write
        self.assertEqual(
            max_concurrent_writes,
            1,
            'Multiple concurrent writes detected, locking failed',
        )

    def test_restore_registry_with_metrics(self):
        """Test that when a registry is restored, the registered LLM is initiated with the restored metrics."""
        service_id = self.generate_unique_id('service-restore')

        # Reset class variables to ensure clean state
        self.reset_registry_class_vars()

        # Create a unique conversation ID for this test
        conversation_id = self.generate_unique_id('conversation-restore')
        user_id = self.generate_unique_id('user-restore')

        # Create a registry and register an LLM
        registry1 = LLMRegistry(
            file_store=self.file_store,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # Register an LLM and add some metrics
        llm1 = registry1.register_llm(service_id, self.llm_config)
        llm1.metrics.add_cost(10.5)  # Add some cost
        llm1.metrics.add_token_usage(
            prompt_tokens=100,
            completion_tokens=50,
            cache_read_tokens=0,
            cache_write_tokens=0,
            context_window=4096,
            response_id='test-response-1',
        )

        # Save the registry
        registry1.save_registry()

        # Reset class variables to simulate a new instance
        self.reset_registry_class_vars()

        # Create a new registry with the same file_store, conversation_id, and user_id
        registry2 = LLMRegistry(
            file_store=self.file_store,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        # Register the same LLM service
        llm2 = registry2.register_llm(service_id, self.llm_config)

        # Verify that the metrics were restored
        self.assertEqual(llm2.metrics.accumulated_cost, 10.5)
        self.assertEqual(llm2.metrics.accumulated_token_usage.prompt_tokens, 100)
        self.assertEqual(llm2.metrics.accumulated_token_usage.completion_tokens, 50)
        self.assertEqual(len(llm2.metrics.costs), 1)
        self.assertEqual(len(llm2.metrics.token_usages), 1)

    def test_multiple_services_combined_metrics(self):
        """Test that multiple services doing LLM completions have their costs accurately reflected in combined metrics."""
        # Register multiple LLM services
        service1 = 'service1'
        service2 = 'service2'
        service3 = 'service3'

        # Register the LLMs
        llm1 = self.registry.register_llm(service1, self.llm_config)
        llm2 = self.registry.register_llm(service2, self.llm_config)
        llm3 = self.registry.register_llm(service3, self.llm_config)

        # Add different costs and token usages to each LLM
        llm1.metrics.add_cost(5.0)
        llm1.metrics.add_token_usage(
            prompt_tokens=100,
            completion_tokens=50,
            cache_read_tokens=0,
            cache_write_tokens=0,
            context_window=4096,
            response_id='response1',
        )

        llm2.metrics.add_cost(7.5)
        llm2.metrics.add_token_usage(
            prompt_tokens=200,
            completion_tokens=75,
            cache_read_tokens=0,
            cache_write_tokens=0,
            context_window=4096,
            response_id='response2',
        )

        llm3.metrics.add_cost(12.25)
        llm3.metrics.add_token_usage(
            prompt_tokens=300,
            completion_tokens=125,
            cache_read_tokens=0,
            cache_write_tokens=0,
            context_window=8192,
            response_id='response3',
        )

        # Get the combined metrics
        combined_metrics = self.registry.get_combined_metrics()

        # Verify the combined metrics
        self.assertEqual(combined_metrics.accumulated_cost, 24.75)  # 5.0 + 7.5 + 12.25
        self.assertEqual(
            combined_metrics.accumulated_token_usage.prompt_tokens, 600
        )  # 100 + 200 + 300
        self.assertEqual(
            combined_metrics.accumulated_token_usage.completion_tokens, 250
        )  # 50 + 75 + 125
        self.assertEqual(
            combined_metrics.accumulated_token_usage.context_window, 8192
        )  # max of all context windows

        # Verify that the individual LLM metrics are unchanged
        self.assertEqual(llm1.metrics.accumulated_cost, 5.0)
        self.assertEqual(llm2.metrics.accumulated_cost, 7.5)
        self.assertEqual(llm3.metrics.accumulated_cost, 12.25)

    def test_request_extraneous_completion(self):
        """Test that requesting an extraneous completion creates a new LLM if needed and saves the registry."""
        service_id = 'extraneous-service'
        messages = [{'role': 'user', 'content': 'Hello, world!'}]

        # Mock the LLM.completion method to return a predictable response
        with patch.object(LLM, 'completion') as mock_completion:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = 'Hello from the LLM!'
            mock_completion.return_value = mock_response

            # Mock the save_registry method to verify it's called
            with patch.object(self.registry, 'save_registry') as mock_save_registry:
                # Request a completion
                response = self.registry.request_extraneous_completion(
                    service_id=service_id,
                    llm_config=self.llm_config,
                    messages=messages,
                )

                # Verify the response
                self.assertEqual(response, 'Hello from the LLM!')

                # Verify that the LLM was created and added to the registry
                self.assertIn(service_id, self.registry.service_to_llm)

                # Verify that save_registry was called
                mock_save_registry.assert_called_once()

    def test_request_existing_service(self):
        """Test that requesting an existing service returns a new LLM with the same metrics."""
        service_id = 'existing-service'

        # Register an LLM and add some metrics
        llm1 = self.registry.register_llm(service_id, self.llm_config)
        llm1.metrics.add_cost(15.0)

        # Request the existing service
        llm2 = self.registry.request_existing_service(service_id, self.llm_config)

        # Verify that a new LLM was created with the same metrics
        self.assertIsNot(llm1, llm2)
        self.assertEqual(llm2.metrics.accumulated_cost, 15.0)

        # Verify that changes to the new LLM's metrics affect the original
        llm2.metrics.add_cost(5.0)
        self.assertEqual(llm1.metrics.accumulated_cost, 20.0)

        # Verify that requesting a non-existent service raises an exception
        with self.assertRaises(Exception) as context:
            self.registry.request_existing_service(
                'non-existent-service', self.llm_config
            )

        self.assertIn('LLM service does not exist', str(context.exception))


if __name__ == '__main__':
    unittest.main()
