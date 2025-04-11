import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor

def compress_model(input_path, output_path):
    # Load the original model
    print("Loading original model...")
    model = joblib.load(input_path)
    
    if not isinstance(model, RandomForestRegressor):
        raise ValueError("Model is not a RandomForestRegressor")
    
    # Create a new model with reduced parameters
    print("Creating compressed model...")
    compressed_model = RandomForestRegressor(
        n_estimators=min(50, model.n_estimators),  # Reduce number of trees
        max_depth=min(10, model.max_depth) if model.max_depth is not None else 10,  # Reduce tree depth
        min_samples_split=5,  # Increase minimum samples to split
        min_samples_leaf=3,   # Increase minimum samples in leaf
        random_state=42
    )
    
    # Get the training data from the original model
    # Note: This assumes the model was trained with the same data structure
    X = np.random.rand(100, 5)  # Placeholder data with same shape as training data
    y = model.predict(X)
    
    # Train the compressed model
    print("Training compressed model...")
    compressed_model.fit(X, y)
    
    # Save the compressed model
    print("Saving compressed model...")
    joblib.dump(compressed_model, output_path, compress=3)  # Use maximum compression
    
    # Compare sizes
    original_size = joblib.load(input_path).__sizeof__()
    compressed_size = compressed_model.__sizeof__()
    print(f"Original model size: {original_size / (1024*1024):.2f} MB")
    print(f"Compressed model size: {compressed_size / (1024*1024):.2f} MB")
    print(f"Compression ratio: {original_size/compressed_size:.2f}x")

if __name__ == "__main__":
    input_model = r"E:\Late-Night\Encoders\rf_model.pkl"
    output_model = r"E:\Late-Night\Encoders\rf_model_compressed.pkl"
    compress_model(input_model, output_model) 