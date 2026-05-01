<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\StockWarehouse;
use App\Models\StockMouvement;
use App\Models\StockInventaire;
use App\Models\StockProduitEntrepot;
use Illuminate\Http\Request;

class StockWarehouseController extends Controller
{
    public function index()   { return response()->json(StockWarehouse::withTrashed()->paginate(50)); }
    public function show($id) { return response()->json(StockWarehouse::withTrashed()->with('stockProduits.product')->findOrFail($id)); }
    public function store(Request $r) { return response()->json(StockWarehouse::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = StockWarehouse::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { StockWarehouse::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class StockMouvementController extends Controller
{
    public function index(Request $r)
    {
        $q = StockMouvement::withTrashed()->with(['product', 'warehouse', 'user']);
        if ($r->filled('warehouse_id')) $q->where('warehouse_id', $r->warehouse_id);
        if ($r->filled('product_id'))   $q->where('product_id', $r->product_id);
        return response()->json($q->latest('date_mouvement')->paginate(100));
    }
    public function show($id) { return response()->json(StockMouvement::withTrashed()->findOrFail($id)); }
    public function store(Request $r) { return response()->json(StockMouvement::create($r->all()), 201); }
    public function destroy($id) { StockMouvement::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class StockInventaireController extends Controller
{
    public function index()   { return response()->json(StockInventaire::withTrashed()->with('warehouse')->paginate(50)); }
    public function show($id) { return response()->json(StockInventaire::withTrashed()->with(['warehouse','items.produit'])->findOrFail($id)); }
    public function store(Request $r) { return response()->json(StockInventaire::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = StockInventaire::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { StockInventaire::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class StockProduitEntrepotController extends Controller
{
    public function index(Request $r)
    {
        $q = StockProduitEntrepot::withTrashed()->with(['product','warehouse']);
        if ($r->filled('warehouse_id')) $q->where('warehouse_id', $r->warehouse_id);
        if ($r->filled('product_id'))   $q->where('product_id', $r->product_id);
        return response()->json($q->paginate(200));
    }
    public function show($id) { return response()->json(StockProduitEntrepot::withTrashed()->findOrFail($id)); }
    public function store(Request $r) { return response()->json(StockProduitEntrepot::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = StockProduitEntrepot::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { StockProduitEntrepot::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
