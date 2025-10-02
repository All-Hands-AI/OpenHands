#!/usr/bin/env julia
import Pkg
Pkg.activate(@__DIR__)
Pkg.instantiate()

using PrayerHandsGenie

PrayerHandsGenie.start()
