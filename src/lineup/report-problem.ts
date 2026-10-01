// A problem found while reading the page or setting the lineup, which needs a person's attention but doesn't stop the run

type ProblemHandler = (message: string) => void;

// `alert` is looked up per call: the headless runner swaps in its own to collect problems
let handleProblem: ProblemHandler = (message) => globalThis.alert(message);

export function reportProblem(message: string) {
  handleProblem(message);
}

export function setProblemHandler(handler: ProblemHandler) {
  handleProblem = handler;
}
