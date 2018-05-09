## alosi_engine python package

### Setup

To install as an editable project:
```
# clone repo
git clone https://github.com/harvard-vpal/adaptive-engine
pip install -e ./adaptive-engine/alosi_engine
```
 
### Usage

#### Using [BaseAdaptiveEngine](https://github.com/harvard-vpal/adaptive-engine/blob/master/alosi_engine/alosi_engine/base_engine.py):

You'll need to subclass BaseAdaptiveEngine and implement all the empty methods. For example:

```
import numpy as np
from alosi_engine import BaseAdaptiveEngine

class LocalAdaptiveEngine(BaseAdaptiveEngine):

    def __init__(self):
        self.Scores = np.array([
            [0, 0, 1.0],
            [0, 1, 0.7],
        ])
        self.Mastery = np.array([
            [0.1, 0.2],
            [0.3, 0.5],
        ])
        self.MasteryPrior = np.array([0.1, 0.1])

    def get_guess(self, activity_id=None):
        GUESS = np.array([
            [0.1, 0.2],
            [0.3, 0.4],
            [0.5, 0.6]
        ])
        if activity_id is not None:
            return GUESS[activity_id]
        else:
            return GUESS
    
    # implement more methods here ...
...

# Usage

# instantiate a new engine subclass instance
engine = LocalAdaptiveEngine()

# Recommend an activity
engine.recommend(learner_id=1)

# Perform learner mastery Bayesian update for a new score
engine.update_from_score(learner_id=0, activity_id=0, score=0.5)

# Perform estimation and update guess/slip/transit matrices and prior mastery:
engine.train()

```
See the full example in [`examples/example_engine.py`](https://github.com/harvard-vpal/adaptive-engine/blob/master/alosi_engine/examples/example_engine.py)

