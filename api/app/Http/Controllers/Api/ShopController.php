<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\ShopClient;
use App\Models\ShopPanier;
use App\Models\ShopExpense;
use Illuminate\Http\Request;

class ShopClientController extends Controller
{
    public function index()   { return response()->json(ShopClient::withTrashed()->paginate(100)); }
    public function show($id) { return response()->json(ShopClient::withTrashed()->with('paniers')->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(ShopClient::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = ShopClient::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { ShopClient::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class ShopPanierController extends Controller
{
    public function index(Request $r)
    {
        $q = ShopPanier::withTrashed()->with(['client','user','produits.product','services.service','paiements']);
        if ($r->filled('pos_id'))  $q->where('pos_id', $r->pos_id);
        if ($r->filled('statut'))  $q->where('statut', $r->statut);
        return response()->json($q->latest('date_vente')->paginate(50));
    }
    public function show($id) { return response()->json(ShopPanier::withTrashed()->with(['client','user','produits.product','services.service','paiements.paymentMode'])->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(ShopPanier::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = ShopPanier::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { ShopPanier::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class ShopExpenseController extends Controller
{
    public function index(Request $r)
    {
        $q = ShopExpense::withTrashed()->with('user');
        if ($r->filled('pos_id')) $q->where('pos_id', $r->pos_id);
        return response()->json($q->latest('date_depense')->paginate(100));
    }
    public function show($id)    { return response()->json(ShopExpense::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(ShopExpense::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = ShopExpense::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { ShopExpense::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
