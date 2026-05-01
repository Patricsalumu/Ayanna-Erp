<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\RestauSalle;
use App\Models\RestauTable;
use App\Models\RestauPanier;
use App\Models\RestauExpense;
use Illuminate\Http\Request;

class RestauSalleController extends Controller
{
    public function index()   { return response()->json(RestauSalle::withTrashed()->with('tables')->paginate(50)); }
    public function show($id) { return response()->json(RestauSalle::withTrashed()->with('tables')->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(RestauSalle::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = RestauSalle::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { RestauSalle::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class RestauTableController extends Controller
{
    public function index()   { return response()->json(RestauTable::withTrashed()->with('salle')->paginate(100)); }
    public function show($id) { return response()->json(RestauTable::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(RestauTable::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = RestauTable::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { RestauTable::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class RestauPanierController extends Controller
{
    public function index(Request $r)
    {
        $q = RestauPanier::withTrashed()->with(['table.salle','user','produits.product','paiements']);
        if ($r->filled('pos_id')) $q->where('pos_id', $r->pos_id);
        if ($r->filled('statut')) $q->where('statut', $r->statut);
        return response()->json($q->latest('date_ouverture')->paginate(50));
    }
    public function show($id) { return response()->json(RestauPanier::withTrashed()->with(['table.salle','user','produits.product','paiements.paymentMode','printedInvoices'])->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(RestauPanier::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = RestauPanier::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { RestauPanier::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class RestauExpenseController extends Controller
{
    public function index(Request $r)
    {
        $q = RestauExpense::withTrashed()->with('user');
        if ($r->filled('pos_id')) $q->where('pos_id', $r->pos_id);
        return response()->json($q->latest('date_depense')->paginate(100));
    }
    public function show($id)    { return response()->json(RestauExpense::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(RestauExpense::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = RestauExpense::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { RestauExpense::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
