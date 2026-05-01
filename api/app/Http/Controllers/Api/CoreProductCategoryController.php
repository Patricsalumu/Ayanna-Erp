<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\CoreProduct;
use App\Models\CoreProductCategory;
use Illuminate\Http\Request;

// ─── CoreProductCategory ─────────────────────────────────────────────────────

class CoreProductCategoryController extends Controller
{
    public function index()       { return response()->json(CoreProductCategory::withTrashed()->paginate(100)); }
    public function show($id)     { return response()->json(CoreProductCategory::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(CoreProductCategory::create($r->all()), 201); }
    public function update(Request $r, $id) {
        $m = CoreProductCategory::withTrashed()->findOrFail($id);
        $m->update($r->all());
        return response()->json($m);
    }
    public function destroy($id)  { CoreProductCategory::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
