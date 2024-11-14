import antlr4 from "antlr4";
import SensorGrammarLexer from "./lib/SensorGrammarLexer.js";
import SensorGrammarParser from "./lib/SensorGrammarParser.js";
import ErrorListener from "./error/ErrorListener.js";
import SensorVisitor from "./SensorVisitor.js";
import store from "./store.js";
import { transformation } from "./SensorVisitorHelper.js";

export function parse(inputStr, debug = false) {
  const chars = new antlr4.InputStream(inputStr);
  const lexer = new SensorGrammarLexer(chars);
  lexer.strictMode = false; // do not use js strictMode

  const tokens = new antlr4.CommonTokenStream(lexer);
  const parser = new SensorGrammarParser(tokens);

  const errorListener = new ErrorListener();
  // Do this after creating the parser and before running it
  parser.removeErrorListeners(); // Remove default ConsoleErrorListener
  parser.addErrorListener(errorListener); // Add custom error listener

  const visitor = new SensorVisitor(store, debug);
  const tree = parser.parse();
  visitor.start(tree);

  // return store.getProduct();
  const res = transformation(store.getProduct());
  store.reset();
  return res;
}
