## SUMMARY ###########################################################################################################
# Unit tests for GPT2TokenGenerator
# - Test Model Loading
# - Test Warm-Up
# - Test Text Generation
# - Test Performance Measurement
## LIBRARIES ###########################################################################################################
import unittest
import os
import sys
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
from tabulate import tabulate
from colorama import Fore, Style, init

## CLASS IMPORTS #####################################################################################################
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))
from localContentAnalyzer import GPT2TokenGenerator

# Initialize colorama for colored output
init(autoreset=True)

## TEST CLASS ########################################################################################################
class TestGPT2TokenGenerator(unittest.TestCase):
    def setUp(self):
        """
        Set up the GPT2TokenGenerator for testing.
        """
        self.generator = GPT2TokenGenerator()
        self.test_prompt = "Once upon a time"
        self.max_length = 50

    def test_load_model_and_tokenizer(self):
        """
        Test that the model and tokenizer are loaded successfully.
        """
        self.generator.load_model_and_tokenizer()
        self.assertIsInstance(self.generator.model, GPT2LMHeadModel)
        self.assertIsInstance(self.generator.tokenizer, GPT2Tokenizer)
        self.assertTrue(self.generator.initialized, "Model and tokenizer should be initialized.")

    def test_warm_up(self):
        """
        Test the warm-up function to ensure it runs without errors.
        """
        self.generator.load_model_and_tokenizer()
        try:
            self.generator.warm_up(self.test_prompt)
        except Exception as e:
            self.fail(f"Warm-up failed with exception: {e}")

    def test_generate_text(self):
        """
        Test the text generation to ensure valid output.
        """
        self.generator.load_model_and_tokenizer()
        generated_text = self.generator.generate_text(self.test_prompt, max_length=self.max_length)
        self.assertIsInstance(generated_text, str, "Generated text should be a string.")
        self.assertGreater(len(generated_text), 0, "Generated text should not be empty.")

    def test_measure_performance(self):
        """
        Test performance measurement to ensure it calculates tokens/second.
        """
        self.generator.load_model_and_tokenizer()
        tokens_per_second = self.generator.measure_performance(self.test_prompt, max_length=self.max_length)
        self.assertIsInstance(tokens_per_second, float, "Tokens per second should be a float.")
        self.assertGreater(tokens_per_second, 0, "Tokens per second should be greater than 0.")

## TEST RUNNER #######################################################################################################
class EnhancedTestRunner:
    def __init__(self):
        self.suite = unittest.TestSuite()
        self.loader = unittest.TestLoader()
        self.result = unittest.TestResult()
        self.failures = []

    def add_tests(self):
        """
        Add all tests from TestGPT2TokenGenerator class.
        """
        self.suite.addTests(self.loader.loadTestsFromTestCase(TestGPT2TokenGenerator))

    def run_tests(self):
        """
        Run the test suite and collect results.
        """
        print(f"{Fore.BLUE}Running Tests...\n")
        self.suite.run(self.result)

        # Display summary
        total_tests = self.result.testsRun
        passed_tests = total_tests - len(self.result.failures)
        failed_tests = len(self.result.failures)
        status_color = Fore.GREEN if failed_tests == 0 else Fore.RED

        # Print summary table
        summary_table = [
            ["Total Tests", total_tests],
            ["Tests Passed", f"{Fore.GREEN}{passed_tests}{Style.RESET_ALL}"],
            ["Tests Failed", f"{Fore.RED}{failed_tests}{Style.RESET_ALL}"]
        ]
        print(tabulate(summary_table, headers=["Metric", "Count"], tablefmt="grid"))

        # Print failure details if any
        if failed_tests > 0:
            print(f"\n{status_color}Failures:")
            failure_details = []
            for failed_test, traceback in self.result.failures:
                failure_details.append([failed_test.id(), traceback.splitlines()[-1]])
                self.failures.append(failed_test.id())
            print(tabulate(failure_details, headers=["Test Name", "Reason"], tablefmt="fancy_grid"))

        print(f"\n{status_color}Test Run Complete.\n")

## MAIN ##############################################################################################################
if __name__ == "__main__":
    runner = EnhancedTestRunner()
    runner.add_tests()
    runner.run_tests()
