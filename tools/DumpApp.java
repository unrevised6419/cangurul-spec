import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.app.cmd.function.CreateFunctionCmd;
import java.io.*;
import java.util.*;

public class DumpApp extends GhidraScript {
  public void run() throws Exception {
    String[] a = getScriptArgs();
    String out = a[0];
    long lo = Long.decode(a[1]), hi = Long.decode(a[2]);
    for (int i = 3; i < a.length; i++) {
      Address ad = toAddr(a[i]);
      if (getFunctionAt(ad) == null) {
        disassemble(ad);
        new CreateFunctionCmd(ad).applyTo(currentProgram);
      }
    }
    analyzeChanges(currentProgram);
    // second pass: create functions at call targets in range not yet functions
    for (int pass = 0; pass < 3; pass++) {
      for (Instruction ins : currentProgram.getListing().getInstructions(toAddr(lo), true)) {
        if (ins.getAddress().getOffset() >= hi) break;
        if (ins.getFlowType().isCall()) for (Address t : ins.getFlows()) {
          if (t.getOffset() >= lo && t.getOffset() < hi && getFunctionAt(t) == null) new CreateFunctionCmd(t).applyTo(currentProgram);
        }
      }
      analyzeChanges(currentProgram);
    }
    DecompInterface di = new DecompInterface();
    di.openProgram(currentProgram);
    PrintWriter pw = new PrintWriter(new FileWriter(out));
    int n = 0;
    for (Function f : currentProgram.getFunctionManager().getFunctions(toAddr(lo), true)) {
      if (f.getEntryPoint().getOffset() >= hi) break;
      DecompileResults r = di.decompileFunction(f, 120, monitor);
      pw.println("// ===== " + f.getName() + " @ " + f.getEntryPoint());
      pw.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// FAILED " + r.getErrorMessage());
      n++;
    }
    pw.close();
    println("dumped " + n);
  }
}
