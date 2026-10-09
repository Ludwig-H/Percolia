// Read-only client of pinned v12: native FULL archive only, no diagnostic text streams.
// Run separately from export_prior.cpp to keep native archive I/O independent of TSV I/O.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <utility>

#include "catalogue/catalogue.hpp"
#include "index/index.hpp"
#include "io/io.hpp"
#include "sched/sched.hpp"
#include "tower/tower.hpp"

using namespace mhgp12;

namespace {
Outcome run(const char* xyz, const char* ids, Order k, u32 threads, const char* directory) {
  const std::array<const char*, 2> input_paths{xyz, ids};
  auto directory_plan = io::OutputDirectory::plan(directory, input_paths);
  if (!directory_plan.ok()) return directory_plan.outcome();
  auto output = std::move(directory_plan).take();
  MemoryBudget budget(MemoryBudget::kUnlimited, 0);
  auto input = io::read_u32le(xyz, ids, budget);
  if (!input.ok()) return input.outcome();
  auto pool = sched::make_pool(sched::PoolParams{threads});
  if (!pool.ok()) return pool.outcome();
  auto prepared = prepare_cloud(input.value().x.span(), input.value().y.span(), input.value().z.span(),
                                input.value().ids.span(), CoordWidth(), budget);
  if (!prepared.ok()) return prepared.outcome();
  auto index = build_index(std::move(prepared).take(), IndexParams{}, budget);
  if (!index.ok()) return index.outcome();
  CatalogueParams params;
  params.kmax = k;
  params.leaf_size = 24;
  auto catalogue = build_catalogue(index.value().cloud(), params, budget, *pool.value());
  if (!catalogue.ok()) return catalogue.outcome();
  auto built = build_tower(index.value(), catalogue.value(), budget, *pool.value());
  if (!built.ok()) return built.outcome();
  const auto& cloud = index.value().cloud();
  const auto& cat = catalogue.value();
  const auto& forests = built.value().forests;
  MHGP12_TRY(tower::validate_forests(forests, budget));
  const tower::FullSource source{&cloud, cat.levels(), tower::catalogue_balls(cat), &forests};
  u64 expected_bytes = 0;
  auto digest = tower::full_digest(source, &expected_bytes);
  if (!digest.ok()) return digest.outcome();
  const auto chars = io::to_hex(digest.value());
  const std::string sha(chars.data(), chars.size());
  auto writer = output.create("full.bin");
  if (!writer.ok()) return writer.outcome();
  MHGP12_TRY(tower::export_full(source, *writer.value()));
  MHGP12_CHECK(writer.value()->size() == expected_bytes && writer.value()->digest() == digest.value(), tower_invariant);
  const std::string manifest = "{\n  \"engine_commit\": \"ac2d5bab814e84db6e1c9340f54995aa9cda58aa\",\n"
    "  \"format\": \"FUL1_native_export\",\n  \"kmax\": " + std::to_string(unsigned(k)) +
    ",\n  \"sites\": " + std::to_string(cloud.sites()) +
    ",\n  \"original_point_ids\": " + std::to_string(cloud.weight()) +
    ",\n  \"full_bytes\": " + std::to_string(expected_bytes) +
    ",\n  \"full_sha256\": \"" + sha + "\",\n  \"diagnostic_text_streams\": false\n}\n";
  MHGP12_TRY(output.commit(manifest));
  std::printf("{\"phase\":\"native_full_export\",\"kmax\":%u,\"sites\":%u,\"bytes\":%llu,\"full_sha256\":\"%s\"}\n",
              unsigned(k), cloud.sites(), (unsigned long long)expected_bytes, sha.c_str());
  return {};
}
} // namespace

int main(int argc, char** argv) {
  if (argc != 6) {
    std::fprintf(stderr, "usage: export_full_only xyz.u32le ids.u32le K threads output_directory\n");
    return 2;
  }
  const unsigned k = unsigned(std::strtoul(argv[3], nullptr, 10));
  const unsigned threads = unsigned(std::strtoul(argv[4], nullptr, 10));
  if (k < 1 || k > 12 || threads < 1 || threads > 1024) return 2;
  const Outcome outcome = guarded([&] { return run(argv[1], argv[2], Order(k), threads, argv[5]); });
  std::printf("{\"phase\":\"exit\",\"status\":\"%s\",\"reason\":\"%s\"}\n",
              std::string(status_name(outcome.status())).c_str(), std::string(reason_name(outcome.reason)).c_str());
  return exit_code(outcome);
}
