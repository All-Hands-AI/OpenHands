module PrayerHandsGenie

export start

using Genie
using Genie.Router: route, GET
using Genie.Renderer.Json: json
using PythonCall: Py, pycall, pyconvert, pyimport

const PROJECT_ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const ROUTES_INITIALIZED = Ref(false)
const SYSTEM_STATS = Ref{Union{Nothing, Py}}(nothing)

function __init__()
    ensure_python_path!()
    SYSTEM_STATS[] = pyimport("openhands.runtime.utils.system_stats")
end

function ensure_python_path!()
    sys = pyimport("sys")
    path_list = sys."path"
    has_path = pycall(path_list.__contains__, Bool, PROJECT_ROOT)
    if !has_path
        path_list.insert(0, PROJECT_ROOT)
    end
    return nothing
end

function setup_routes()
    if ROUTES_INITIALIZED[]
        return nothing
    end

    route("/alive", method = GET) do
        json(Dict("status" => "ok"))
    end

    route("/health", method = GET) do
        "OK"
    end

    route("/server_info", method = GET) do
        stats_mod = SYSTEM_STATS[]
        stats_mod === nothing && throw(ErrorException("Python system stats module not initialised"))
        info = stats_mod.get_system_info()
        converted = pyconvert(Dict{String, Any}, info)
        json(converted)
    end

    ROUTES_INITIALIZED[] = true
    return nothing
end

function start(; host::AbstractString = "0.0.0.0", port::Integer = 8001, async::Bool = false)
    ensure_python_path!()
    setup_routes()

    Genie.up(host = host, port = port, async = async)
end

end # module
