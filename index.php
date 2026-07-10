<?php
/**
 * BeWordSmith — PHP backend for Apache / nginx / shared (cPanel) hosting.
 *
 * Same UI and content as the Python server (server.py); this is the drop-in
 * option for hosts that give you PHP by default and no long-running process.
 *
 *   • "/"            -> the shell (UI), read from _app/shell.html
 *   • "?api=tree"    -> JSON menu tree (folder walk of content/)
 *   • everything else is a real file, served by the web server directly.
 *
 * Uses relative URLs, so it works in any subdirectory with no rewrites.
 */

$ROOT = __DIR__;

// ---- config (config.json overrides these defaults) -------------------------
$DEFAULTS = [
    "site_title"    => "BeWordSmith",
    "site_subtitle" => "Docs & guides",
    "content_dir"   => "content",
    "page_word"     => "page",
    "accent"        => "#FF671D",
    "home"          => "",
    "donate_url"    => "",
    "menu"          => [],
];
$cfg = $DEFAULTS;
$cf = $ROOT . "/config.json";
if (is_file($cf)) {
    $user = json_decode(file_get_contents($cf), true);
    if (is_array($user)) {
        foreach ($DEFAULTS as $k => $_) {
            if (array_key_exists($k, $user)) $cfg[$k] = $user[$k];
        }
    }
}
$CONTENT_DIR = (string)$cfg["content_dir"];
$MENU = is_array($cfg["menu"]) ? $cfg["menu"] : [];

// ---- php -S static passthrough (serve real files as-is) --------------------
if (php_sapi_name() === "cli-server") {
    $p = rawurldecode(parse_url($_SERVER["REQUEST_URI"], PHP_URL_PATH));
    if ($p !== "/" && $p !== "" && is_file($ROOT . $p)) return false;
}

// ---- helpers ---------------------------------------------------------------
function display_name($n) { return preg_replace('/^\s*\d+\s*[.)_-]\s*/u', '', $n); }
function clean_title($f)  { return display_name(preg_replace('/\.md$/i', '', $f)); }
function prefix_order($n) { return preg_match('/^\s*(\d+)\s*[.)_-]/u', $n, $m) ? (float)$m[1] : null; }

function list_dirs($dir) {
    $out = [];
    foreach (@scandir($dir) ?: [] as $e) {
        if ($e[0] === ".") continue;
        if (in_array($e, ["_resources", "_app", "_help", "pluginAssets"], true)) continue;
        if (is_dir("$dir/$e")) $out[] = $e;
    }
    return $out;
}
function list_md($dir) {
    $out = [];
    foreach (@scandir($dir) ?: [] as $e) {
        if (is_file("$dir/$e") && strtolower(substr($e, -3)) === ".md") $out[] = $e;
    }
    return $out;
}

/** Sort names by (explicit order → numeric prefix → nothing), then natural. */
function sorted_items($names, $path_prefix, $is_file, $MENU) {
    $arr = [];
    foreach ($names as $name) {
        $path = "$path_prefix/$name";
        $ov = isset($MENU[$path]) && is_array($MENU[$path]) ? $MENU[$path] : [];
        $order = array_key_exists("order", $ov) && is_numeric($ov["order"]) ? (float)$ov["order"] : prefix_order($name);
        $label = (isset($ov["label"]) && $ov["label"] !== "")
            ? $ov["label"]
            : ($is_file ? clean_title($name) : display_name($name));
        $arr[] = ["name" => $name, "path" => $path, "label" => $label,
                  "order" => $order, "dn" => display_name($is_file ? preg_replace('/\.md$/i', '', $name) : $name)];
    }
    usort($arr, function ($a, $b) {
        $ga = $a["order"] === null ? 1 : 0;
        $gb = $b["order"] === null ? 1 : 0;
        if ($ga !== $gb) return $ga - $gb;
        if ($ga === 0 && $a["order"] != $b["order"]) return $a["order"] <=> $b["order"];
        return strnatcasecmp($a["dn"], $b["dn"]);
    });
    return $arr;
}

function build_tree($ROOT, $CONTENT_DIR, $MENU) {
    $base = "$ROOT/$CONTENT_DIR";
    $sections = [];
    foreach (sorted_items(list_dirs($base), $CONTENT_DIR, false, $MENU) as $s) {
        $sdir = "$base/{$s['name']}";
        $pages = [];
        foreach (sorted_items(list_md($sdir), $s["path"], true, $MENU) as $p)
            $pages[] = ["title" => $p["label"], "path" => $p["path"], "type" => "md"];
        $groups = [];
        foreach (sorted_items(list_dirs($sdir), $s["path"], false, $MENU) as $g) {
            $gdir = "$base/{$s['name']}/{$g['name']}";
            $gp = [];
            foreach (sorted_items(list_md($gdir), $g["path"], true, $MENU) as $p)
                $gp[] = ["title" => $p["label"], "path" => $p["path"], "type" => "md"];
            if ($gp) $groups[] = ["title" => $g["label"], "pages" => $gp];
        }
        if ($pages || $groups)
            $sections[] = ["title" => $s["label"], "pages" => $pages, "groups" => $groups];
    }
    return ["sections" => $sections];
}

// ---- routes ----------------------------------------------------------------
if (isset($_GET["api"]) && $_GET["api"] === "tree") {
    header("Content-Type: application/json; charset=utf-8");
    echo json_encode(build_tree($ROOT, $CONTENT_DIR, $MENU));
    exit;
}

// ---- accent-derived colors -------------------------------------------------
function accent_parts($hex) {
    if (!preg_match('/^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/', (string)$hex)) $hex = "#FF671D";
    $h = ltrim($hex, "#");
    if (strlen($h) === 3) $h = $h[0].$h[0].$h[1].$h[1].$h[2].$h[2];
    $r = hexdec(substr($h, 0, 2)); $g = hexdec(substr($h, 2, 2)); $b = hexdec(substr($h, 4, 2));
    $lit = fn($c) => (int)round($c + (255 - $c) * 0.45);
    return [
        "hex" => "#$h",
        "rgb" => "$r, $g, $b",
        "hi"  => sprintf("#%02x%02x%02x", $lit($r), $lit($g), $lit($b)),
    ];
}
$ac = accent_parts($cfg["accent"]);

// ---- serve the shell -------------------------------------------------------
$tpl = file_get_contents("$ROOT/_app/shell.html");
$repl = [
    "__SITE_TITLE__"    => $cfg["site_title"],
    "__SITE_SUBTITLE__" => $cfg["site_subtitle"],
    "__PAGE_WORD__"     => $cfg["page_word"],
    "__DONATE_URL__"    => str_replace('"', '', (string)($cfg["donate_url"] ?? "")),
    "__HOME__"          => str_replace('"', '\\"', (string)$cfg["home"]),
    "__ACCENT_RGB__"    => $ac["rgb"],
    "__ACCENT_HI__"     => $ac["hi"],
    "__ACCENT__"        => $ac["hex"],
    "__ASSET__"         => ".",          // relative — works in any subdirectory
    "__TREE__"          => "?api=tree",
];
header("Content-Type: text/html; charset=utf-8");
echo strtr($tpl, $repl);
