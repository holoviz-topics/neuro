import pandas as pd
import numpy as np
import colorcet as cc

def create_random_ranges(n_total_seconds: int, n_categories: int, 
                             n_total_annotations: int, duration: int = 1) -> pd.DataFrame:
    """
    Generate a DataFrame containing annotations for a range of categories over a specified time duration.

    Parameters
    ----------
    n_total_seconds : int
        The total time duration in seconds over which annotations are to be created.
    n_categories : int
        The number of distinct categories to be annotated.
    n_total_annotations : int
        The total number of annotations to be created.
    duration : int, optional
        The duration of each annotation in seconds. Defaults to 1.

    Returns
    -------
    pd.DataFrame
        A DataFrame with the following columns:
        - 'start': Start time of the annotation.
        - 'end': End time of the annotation.
        - 'category': Category of the annotation.
        - 'color': Color assigned to the category of the annotation.
        
        Each row in the DataFrame represents a single annotation, with 'start' and 'end' times, 
        'category' and the 'color' associated with that 'category'.

    Examples
    --------
    >>> annotations_df = create_range_annotations(100, 3, 5)
    >>> annotations_df.sample(5)
       start  end category    color
    0      8    9        A  #0072B2
    1     25   26        C  #D55E00
    2     41   42        B  #009E73
    3     57   58        C  #D55E00
    4     73   74        A  #0072B2

    """
    ...

    start_times = np.sort(np.random.randint(0, n_total_seconds - duration, n_total_annotations))
    
    # Ensure the annotations are non-overlapping
    for i in range(1, len(start_times)):
        if start_times[i] < start_times[i-1] + duration:
            start_times[i] = start_times[i-1] + duration
    end_times = start_times + duration
    categories = np.random.choice(list(string.ascii_uppercase)[:n_categories], n_total_annotations)
    
    df = pd.DataFrame({
        'start': start_times,
        'end': end_times,
        'category': categories
    })
    df['category'] = df['category'].astype('category')
    
    unique_categories = df['category'].cat.categories
    color_map = dict(zip(unique_categories, cc.glasbey[:len(unique_categories)]))
    df['color'] = df['category'].map(color_map)
    df['color'] = df['color'].astype('category')
    
    return df