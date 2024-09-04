import numpy as np

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def get_metrics(y_test, y_preds):
    mae = mean_absolute_error(y_test, y_preds)
    mse = mean_squared_error(y_test, y_preds)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_preds)

    print(f'Mean Absolute Error (MAE): {mae:.3f}')
    print(f'Mean Squared Error (MSE): {mse:.3f}')
    print(f'Root Mean Squared Error (RMSE): {rmse:.3f}')
    print(f'R-squared (R²): {r2:.3f}')

    return {
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "r2": r2
    }