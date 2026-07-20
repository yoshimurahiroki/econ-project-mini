find_project_root <- function(path = getwd()) {
  path <- normalizePath(path, mustWork = TRUE)
  repeat {
    if (file.exists(file.path(path, "rproject.toml"))) {
      return(path)
    }
    parent <- dirname(path)
    if (identical(parent, path)) {
      stop("Could not find rproject.toml.", call. = FALSE)
    }
    path <- parent
  }
}

project_root <- find_project_root()
rv_library <- local({
  previous_directory <- setwd(project_root)
  on.exit(setwd(previous_directory))
  system2("rv", "library", stdout = TRUE)
})

if (length(rv_library) == 1L && dir.exists(rv_library)) {
  .libPaths(unique(c(rv_library, .libPaths())))
}
