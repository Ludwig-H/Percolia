// Read-only client of the pinned v12 CPU reference engine.
// Exports genuine FULL nodes and strong P_b incidences for an external geometry-prior experiment.
// This is not the unported H^r point hierarchy, a native prior API, or a certified flat extraction.
#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <optional>

#include "catalogue/catalogue.hpp"
#include "index/index.hpp"
#include "io/io.hpp"
#include "sched/sched.hpp"
#include "tower/tower.hpp"

using namespace mhgp12;

namespace {
bool parse_u128(const std::string& text, u128& out) {
  out = 0;
  std::size_t j = 0;
  unsigned base = 10;
  if (text.size() > 2 && text[0] == '0' && (text[1] == 'x' || text[1] == 'X')) { base = 16; j = 2; }
  if (j == text.size()) return false;
  for (; j < text.size(); ++j) {
    const char c = text[j];
    const unsigned d = c >= '0' && c <= '9' ? unsigned(c - '0')
                     : c >= 'a' && c <= 'f' ? unsigned(c - 'a' + 10)
                     : c >= 'A' && c <= 'F' ? unsigned(c - 'A' + 10) : base;
    if (d >= base || out > (~u128{0} - d) / base) return false;
    out = out * base + d;
  }
  return true;
}
std::string decimal_u128(u128 value) {
  if (value == 0) return "0";
  std::string out;
  while (value) { out.push_back(char('0' + value % 10)); value /= 10; }
  std::reverse(out.begin(), out.end());
  return out;
}
template <class Integer>
std::string exact_hex(const Integer& value) {
  const auto wide = num::to_wide(value);
  std::ostringstream text;
  if (wide.neg) text << '-';
  text << "0x";
  bool started = false;
  for (std::size_t j = wide.words.size(); j-- > 0;) {
    if (!started && wide.words[j] == 0) continue;
    if (!started) { text << std::hex << wide.words[j]; started = true; }
    else text << std::hex << std::setw(16) << std::setfill('0') << wide.words[j];
  }
  if (!started) text << '0';
  return text.str();
}

Outcome run(const char* xyz, const char* ids, Order k, u32 threads, const std::string& prefix,
            bool do_cut, u128 cut_num, u128 cut_den, bool do_export_full) {
  std::optional<io::OutputDirectory> full_directory;
  if (do_export_full) {
    const std::string path = prefix + ".full_export";
    const std::array<const char*, 2> inputs{xyz, ids};
    auto plan = io::OutputDirectory::plan(path.c_str(), inputs);
    if (!plan.ok()) return plan.outcome();
    full_directory.emplace(std::move(plan).take());
  }
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
  const Tower& tower = built.value();
  MHGP12_TRY(tower::validate_forests(tower.forests, budget));
  const auto& forest = tower.forests.orders[k - 1];
  const auto& cloud = index.value().cloud();
  const auto& cat = catalogue.value();

  // Exact rational radii-squared in input quantization units. No floating-point cut decisions.
  std::ofstream levels(prefix + ".levels.tsv");
  levels << "rank\tradius_squared_numerator_hex\tradius_squared_denominator_hex\n";
  for (u32 rank = 0; rank < cat.levels().size(); ++rank) {
    const auto& level = cat.levels()[rank];
    levels << rank << '\t' << exact_hex(level.numerator()) << '\t' << exact_hex(level.denominator()) << '\n';
  }
  u32 cut_rank = kNone;
  if (do_cut) {
    auto cut_level = num::Level::make(num::Wide<2>::from_u128(cut_num), num::Wide<2>::from_u128(cut_den));
    if (!cut_level.ok()) return cut_level.outcome();
    u32 lo = 0, hi = static_cast<u32>(cat.levels().size());
    while (lo < hi) {
      const u32 mid = lo + (hi - lo) / 2;
      if (num::compare(cat.levels()[mid], cut_level.value()) <= 0) lo = mid + 1;
      else hi = mid;
    }
    MHGP12_CHECK(lo > 0, tower_invariant); // level zero is included by every nonnegative radius.
    cut_rank = lo - 1;
  }

  // All original PointIds are retained; merged quantized sites are never silently assigned weight one.
  std::ofstream sites(prefix + ".sites.tsv");
  sites << "site\tpoint_id\tx_u\ty_u\tz_u\n";
  for (u32 s = 0; s < cloud.sites(); ++s)
    for (PointId p : cloud.points(SiteIdx{s}))
      sites << s << '\t' << idx(p) << '\t' << cloud.x()[s] << '\t' << cloud.y()[s] << '\t' << cloud.z()[s] << '\n';

  std::ofstream nodes(prefix + ".nodes.tsv");
  nodes << "node\tparent\trank\tbirth_key\n";
  for (u32 v = 0; v < forest.nodes(); ++v)
    nodes << v << '\t' << forest.parent[v] << '\t' << forest.rank[v] << '\t'
          << (v < forest.births ? forest.birth_key[v] : kNone) << '\n';

  // Per-order forests include K1 point births, even when the requested diagnostic incidences are K3/K5.
  for (Order order = 1; order <= k; ++order) {
    const auto& f = tower.forests.orders[order - 1];
    std::ofstream order_nodes(prefix + ".nodes_k" + std::to_string(unsigned(order)) + ".tsv");
    order_nodes << "node\tparent\trank\tbirth_key\n";
    for (u32 v = 0; v < f.nodes(); ++v)
      order_nodes << v << '\t' << f.parent[v] << '\t' << f.rank[v] << '\t'
                  << (v < f.births ? f.birth_key[v] : kNone) << '\n';
    order_nodes.close();
    MHGP12_CHECK(order_nodes.good(), output_unwritable);
  }

  if (do_cut) {
    const auto& f = tower.forests.orders[0];
    std::ofstream point_cut(prefix + ".cut_k1.tsv");
    point_cut << "site\tnode\n";
    for (u32 v = 0; v < f.births; ++v) {
      auto at = tower::component_at(f, v, cut_rank);
      if (!at.ok()) return at.outcome();
      point_cut << f.birth_key[v] << '\t' << at.value() << '\n';
    }
    point_cut.close();
    MHGP12_CHECK(point_cut.good(), output_unwritable);
  }

  std::ofstream incidences(prefix + ".incidences.tsv");
  incidences << "site\tnode\trank\tball\n";
  std::ofstream cut_incidences;
  if (do_cut) {
    cut_incidences.open(prefix + ".cut_k" + std::to_string(unsigned(k)) + "_incidences.tsv");
    cut_incidences << "site\tnode\trank\tball\n";
  }
  u64 emitted = 0;
  u64 cut_emitted = 0;
  if (k == 1) {
    for (u32 v = 0; v < forest.births; ++v) {
      incidences << forest.birth_key[v] << '\t' << v << "\t0\t" << kNone << '\n';
      ++emitted;
    }
  } else {
    // Same strong-incidence criterion as the pinned v11 points/incidences.cpp.
    // A strong window ball has p + qmin <= k; P_b is interior union shell, NOT just its <=4-point S*.
    const auto balls = cat.balls_data();
    for (u32 b = 0; b < cat.balls(); ++b) {
      const auto& ball = balls[b];
      if (u64{ball.p} + ball.qmin > k) continue;
      const u32 target = tower.resolution.window_target(BallIdx{b}, k);
      if (target == kNoTarget) continue;
      const u32 t = target_index(target);
      u32 v = kNone;
      if (target_is_cell(target)) {
        MHGP12_CHECK(t < forest.cell_node.size(), tower_invariant);
        v = forest.cell_node[t];
      } else {
        MHGP12_CHECK(t < forest.birth_node.size(), tower_invariant);
        v = forest.birth_node[t];
      }
      MHGP12_CHECK(v < forest.nodes(), tower_invariant);
      const u32 rank = idx(ball.rank);
      MHGP12_CHECK(forest.rank[v] <= rank, tower_invariant);
      MHGP12_CHECK(forest.parent[v] == kNone || forest.rank[forest.parent[v]] > rank, tower_invariant);
      u32 cut_node = v;
      if (do_cut && rank <= cut_rank)
        while (forest.parent[cut_node] != kNone && forest.rank[forest.parent[cut_node]] <= cut_rank)
          cut_node = forest.parent[cut_node];
      for (const auto part : {cat.interior(BallIdx{b}), cat.shell(BallIdx{b})})
        for (SiteIdx s : part) {
          incidences << idx(s) << '\t' << v << '\t' << rank << '\t' << b << '\n';
          ++emitted;
          if (do_cut && rank <= cut_rank) {
            cut_incidences << idx(s) << '\t' << cut_node << '\t' << rank << '\t' << b << '\n';
            ++cut_emitted;
          }
        }
    }
  }

  // Supports are provided for provenance/diagnostics, not used as a substitute for cluster point sets.
  std::ofstream supports(prefix + ".birth_support.tsv");
  supports << "node\tball\tsite\n";
  if (k > 1)
    for (u32 v = 0; v < forest.births; ++v) {
      const u32 b = forest.birth_key[v];
      const auto& ball = cat.balls_data()[b];
      for (u32 q = 0; q < ball.qmin; ++q)
        supports << v << '\t' << b << '\t' << idx(ball.support[q]) << '\n';
    }

  // Close every diagnostic stream before the native transactional export opens/closes its own files.
  // The TSV exports must already be complete before the FULL archive is published.
  sites.close(); nodes.close(); incidences.close(); supports.close(); levels.close();
  if (do_cut) cut_incidences.close();
  MHGP12_CHECK(sites.good() && nodes.good() && incidences.good() && supports.good() && levels.good()
               && (!do_cut || cut_incidences.good()), output_unwritable);

  const tower::FullSource source{&cloud, cat.levels(), tower::catalogue_balls(cat), &tower.forests};
  u64 full_bytes = 0;
  auto digest = tower::full_digest(source, &full_bytes);
  if (!digest.ok()) return digest.outcome();
  const auto sha_chars = io::to_hex(digest.value());
  const std::string sha(sha_chars.data(), sha_chars.size());
  if (full_directory) {
    auto writer = full_directory->create("full.bin");
    if (!writer.ok()) return writer.outcome();
    MHGP12_TRY(tower::export_full(source, *writer.value()));
    MHGP12_CHECK(writer.value()->size() == full_bytes && writer.value()->digest() == digest.value(), tower_invariant);
    std::ostringstream manifest;
    manifest << "{\n  \"engine_commit\": \"ac2d5bab814e84db6e1c9340f54995aa9cda58aa\",\n"
             << "  \"format\": \"FUL1_native_export\",\n  \"kmax\": " << unsigned(k)
             << ",\n  \"full_sha256\": \"" << sha << "\",\n  \"full_bytes\": " << full_bytes
             << ",\n  \"sites\": " << cloud.sites() << ",\n  \"cut_does_not_modify_FULL\": true\n}\n";
    MHGP12_TRY(full_directory->commit(manifest.str()));
  }
  std::ofstream stats(prefix + ".stats.json");
  stats << "{\n  \"engine_commit\": \"ac2d5bab814e84db6e1c9340f54995aa9cda58aa\",\n"
        << "  \"object\": \"native_full_pi0\",\n  \"k\": " << unsigned(k)
        << ",\n  \"sites\": " << cloud.sites() << ",\n  \"original_point_ids\": " << cloud.weight()
        << ",\n  \"nodes\": " << forest.nodes() << ",\n  \"births\": " << forest.births
        << ",\n  \"root\": " << forest.root << ",\n  \"strong_incidences\": " << emitted
        << ",\n  \"full_sha256\": \"" << sha << "\",\n  \"full_bytes\": " << full_bytes
        << ",\n  \"point_view\": \"external_strong_incidence_unions_not_Hr\",\n"
        << "  \"cut_enabled\": " << (do_cut ? "true" : "false")
        << ",\n  \"cut_radius_squared_quantized_numerator\": \"" << decimal_u128(cut_num) << '"'
        << ",\n  \"cut_radius_squared_quantized_denominator\": \"" << decimal_u128(cut_den) << '"'
        << ",\n  \"cut_rank\": " << cut_rank
        << ",\n  \"cut_strong_incidences\": " << cut_emitted
        << ",\n  \"native_FULL_exported\": " << (do_export_full ? "true" : "false")
        << ",\n  \"prior_affects_engine\": false\n}\n";
  stats.close();
  MHGP12_CHECK(stats.good(), output_unwritable);
  std::printf("{\"phase\":\"export\",\"k\":%u,\"sites\":%u,\"nodes\":%u,\"incidences\":%llu}\n",
              unsigned(k), cloud.sites(), forest.nodes(), (unsigned long long)emitted);
  return {};
}
} // namespace

int main(int argc, char** argv) {
  const bool do_export_full = argc > 1 && std::string(argv[argc - 1]) == "--export-full";
  const int positional = argc - (do_export_full ? 1 : 0);
  if (positional != 6 && positional != 8) {
    std::fprintf(stderr, "usage: export_prior xyz.u32le ids.u32le K threads output_prefix [cut_radius_squared_numerator cut_denominator] [--export-full]\n");
    return 2;
  }
  const unsigned k = unsigned(std::strtoul(argv[3], nullptr, 10));
  const unsigned threads = unsigned(std::strtoul(argv[4], nullptr, 10));
  if (k < 1 || k > 12 || threads < 1 || threads > 1024) return 2;
  u128 cut_num = 0, cut_den = 1;
  if (positional == 8 && (!parse_u128(argv[6], cut_num) || !parse_u128(argv[7], cut_den))) return 2;
  if (cut_den == 0) return 2;
  const Outcome outcome = guarded([&] { return run(argv[1], argv[2], Order(k), threads, argv[5], positional == 8, cut_num, cut_den, do_export_full); });
  std::printf("{\"phase\":\"exit\",\"status\":\"%s\",\"reason\":\"%s\"}\n",
              std::string(status_name(outcome.status())).c_str(), std::string(reason_name(outcome.reason)).c_str());
  return exit_code(outcome);
}
