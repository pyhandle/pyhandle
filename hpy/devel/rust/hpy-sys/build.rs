use std::env;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

fn main() {
    println!("cargo:rerun-if-changed=include/");
    println!("cargo:rerun-if-changed=src/runtime/");

    let mut builder = bindgen::Builder::default()
        .header("include/hpy.h")
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .clang_arg("-Iinclude/")
        .allowlist_type("HPy.*")
        .allowlist_type("_HPy.*")
        .allowlist_type("Py.*")
        .allowlist_type("_Py.*")
        .allowlist_function("HPy.*")
        .allowlist_function("_HPy.*")
        .allowlist_function("Py.*")
        .allowlist_function("_Py.*")
        .allowlist_var("HPy.*")
        .allowlist_var("_HPy.*")
        .allowlist_var("Py.*")
        .allowlist_var("_Py.*");

    if cfg!(feature = "abi-cpython") {
        builder = builder.clang_arg("-DHPY_ABI_CPYTHON".to_string());
    }
    if cfg!(feature = "abi-universal") {
        builder = builder.clang_arg("-DHPY_ABI_UNIVERSAL".to_string());
    }
    if cfg!(feature = "abi-hybrid") {
        builder = builder.clang_arg("-DHPY_ABI_HYBRID".to_string());
    }

    let python = env::var("HPY_PYTHON").unwrap_or_else(|_| "python3".to_string());
    let python_include = run_python_script(
        python,
        "import sysconfig; print(sysconfig.get_path('include'), end='')",
    )
    .unwrap();
    if cfg!(any(feature = "abi-cpython", feature = "abi-hybrid")) {
        builder = builder.clang_arg(format!("-I{}", python_include));
    }

    let bindings = builder
        .generate()
        // Unwrap the Result and panic on failure.
        .expect("Unable to generate bindings");

    // Write the bindings to the $OUT_DIR/bindings.rs file.
    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");

    build_hpy(&python_include);
}

fn build_hpy(python_include: &str) {
    let version = format!(
        r#"
// automatically generated build.rs
#define HPY_VERSION "{}"
#define HPY_GIT_REVISION "unknown"
        "#,
        env!("CARGO_PKG_VERSION"),
    );
    fs::write("include/hpy/version.h", version).unwrap();

    let extra_sources = [
        "src/runtime/argparse.c",
        "src/runtime/buildvalue.c",
        "src/runtime/helpers.c",
    ];
    let ctx_sources = [
        "src/runtime/ctx_bytes.c",
        "src/runtime/ctx_call.c",
        "src/runtime/ctx_capsule.c",
        "src/runtime/ctx_err.c",
        "src/runtime/ctx_module.c",
        "src/runtime/ctx_object.c",
        "src/runtime/ctx_type.c",
        "src/runtime/ctx_tracker.c",
        "src/runtime/ctx_listbuilder.c",
        "src/runtime/ctx_tuple.c",
        "src/runtime/ctx_tuplebuilder.c",
    ];

    let mut build = cc::Build::new();
    build.includes([python_include, "include"]);
    if cfg!(feature = "abi-cpython") {
        build
            .files(extra_sources)
            .files(ctx_sources)
            .define("HPY_ABI_CPYTHON", None)
            .compile("hpy-cpython");
    }
    if cfg!(feature = "abi-universal") {
        build
            .files(extra_sources)
            .define("HPY_ABI_UNIVERSAL", None)
            .compile("hpy-universal");
    }
    if cfg!(feature = "abi-hybrid") {
        build
            .files(extra_sources)
            .define("HPY_ABI_HYBRID", None)
            .compile("hpy-hybrid");
    }
}

/// Run a python script using the specified interpreter binary.
fn run_python_script(interpreter: impl AsRef<Path>, script: &str) -> Result<String, String> {
    let interpreter = interpreter.as_ref();
    let out = Command::new(interpreter)
        .env("PYTHONIOENCODING", "utf-8")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .and_then(|mut child| {
            child
                .stdin
                .as_mut()
                .expect("piped stdin")
                .write_all(script.as_bytes())?;
            child.wait_with_output()
        });

    match out {
        Err(err) => Err(format!(
            "failed to run the Python interpreter at {}: {}",
            interpreter.display(),
            err
        )),
        Ok(ok) if !ok.status.success() => Err(format!(
            "Python script failed: {}",
            String::from_utf8(ok.stderr).expect("failed to parse Python script stderr as utf-8")
        )),
        Ok(ok) => Ok(
            String::from_utf8(ok.stdout).expect("failed to parse Python script stdout as utf-8")
        ),
    }
}
