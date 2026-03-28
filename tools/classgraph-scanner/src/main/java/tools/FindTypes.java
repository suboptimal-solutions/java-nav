package tools;

import io.github.classgraph.ClassGraph;
import io.github.classgraph.ClassInfoList;
import io.github.classgraph.ScanResult;

/**
 * Scans bytecode to find implementations of interfaces or subclasses.
 *
 * Usage:
 *   java -cp scanner.jar tools.FindTypes impls <classpath> <classname>
 *   java -cp scanner.jar tools.FindTypes subtypes <classpath> <classname>
 */
public class FindTypes {

    public static void main(String[] args) {
        if (args.length != 3) {
            System.err.println("Usage: FindTypes <impls|subtypes> <classpath> <classname>");
            System.exit(1);
        }

        String mode = args[0];
        String classpath = args[1];
        String className = args[2];

        try (ScanResult scan = new ClassGraph()
                .enableClassInfo()
                .overrideClasspath(classpath)
                .scan()) {

            ClassInfoList results;
            if ("impls".equals(mode)) {
                results = scan.getClassesImplementing(className);
            } else if ("subtypes".equals(mode)) {
                results = scan.getSubclasses(className);
            } else {
                System.err.println("Unknown mode: " + mode + " (use 'impls' or 'subtypes')");
                System.exit(1);
                return;
            }

            for (var ci : results) {
                System.out.println(ci.getName());
            }
        }
    }
}
