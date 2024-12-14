## SUMMARY ###########################################################################################################
# Class: GPT2TokenGenerator
# - load_model_and_tokenizer: Load GPT-2 model and tokenizer
# - warm_up: Perform a warm-up run for optimized performance
# - generate_text: Generate text using GPT-2
# - measure_performance: Measure token generation performance
## LIBRARIES ###########################################################################################################
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import time
## CONFIGURATION #######################################################################################################
torch.backends.quantized.engine = 'qnnpack'

## CLASSES ###########################################################################################################
class GPT2TokenGenerator:
    def __init__(self, model_name="gpt2"):
        """
        Initialize GPT-2 Token Generator with specified model.
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.initialized = False

    def load_model_and_tokenizer(self):
        """
        Load the GPT-2 model and tokenizer.
        """
        print("Loading model and tokenizer...")
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
        self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
        self.model = torch.quantization.quantize_dynamic(self.model, {torch.nn.Linear}, dtype=torch.qint8)
        self.model.eval()
        self.model.to("cpu")
        self.initialized = True
        print("Model loaded and optimized for speed.")

    def warm_up(self, input_text):
        """
        Perform a warm-up run to optimize performance.
        """
        if not self.initialized:
            raise RuntimeError("Model and tokenizer must be loaded first.")
        
        print("Warming up...")
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to("cpu")
        attention_mask = torch.ones_like(input_ids)
        _ = self.model.generate(input_ids, attention_mask=attention_mask, max_length=50)

    def generate_text(self, input_text, max_length=512):
        """
        Generate text based on the input prompt.

        Parameters:
        - input_text (str): Prompt for text generation
        - max_length (int): Maximum length of generated text

        Returns:
        - generated_text (str): Generated text from the model
        """
        if not self.initialized:
            raise RuntimeError("Model and tokenizer must be loaded first.")

        print("Generating text...")
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to("cpu")
        attention_mask = torch.ones_like(input_ids)
        output = self.model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            do_sample=True
        )
        return self.tokenizer.decode(output[0], skip_special_tokens=True)

    def measure_performance(self, input_text, max_length=512):
        """
        Measure the performance of token generation.

        Parameters:
        - input_text (str): Prompt for text generation
        - max_length (int): Maximum length of generated text

        Returns:
        - tokens_per_second (float): Tokens generated per second
        """
        if not self.initialized:
            raise RuntimeError("Model and tokenizer must be loaded first.")
        
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt").to("cpu")
        attention_mask = torch.ones_like(input_ids)

        start_time = time.time()
        output = self.model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
            do_sample=True
        )
        end_time = time.time()

        total_tokens = output.shape[1] - input_ids.shape[1]
        elapsed_time = end_time - start_time
        tokens_per_second = total_tokens / elapsed_time
        return tokens_per_second

## FUNCTIONS #########################################################################################################
def main():
    """
    Main function to demonstrate GPT-2 text generation.
    """
    generator = GPT2TokenGenerator()
    generator.load_model_and_tokenizer()

    input_text = "Provide feedback on best practices of developing unit tests"
    generator.warm_up(input_text)

    print("Measuring performance...")
    tokens_per_second = generator.measure_performance(input_text)
    print(f"\nPerformance: {tokens_per_second:.2f} tokens/second")

    print("\nGenerated Text:")
    generated_text = generator.generate_text(input_text)
    print(generated_text)

## MAIN ##############################################################################################################
if __name__ == "__main__":
    main()
