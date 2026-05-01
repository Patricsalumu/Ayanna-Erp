<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\CoreFournisseur;
use App\Models\AchatCommande;
use App\Models\AchatCommandeLigne;
use App\Models\AchatDepense;
use Illuminate\Http\Request;

class CoreFournisseurController extends Controller
{
    public function index()   { return response()->json(CoreFournisseur::withTrashed()->paginate(100)); }
    public function show($id) { return response()->json(CoreFournisseur::withTrashed()->with('commandes')->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(CoreFournisseur::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = CoreFournisseur::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { CoreFournisseur::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class AchatCommandeController extends Controller
{
    public function index(Request $r)
    {
        $q = AchatCommande::withTrashed()->with(['fournisseur', 'lignes.produit', 'depenses']);
        if ($r->filled('fournisseur_id')) $q->where('fournisseur_id', $r->fournisseur_id);
        if ($r->filled('etat'))           $q->where('etat', $r->etat);
        return response()->json($q->latest()->paginate(50));
    }

    public function show($id) { return response()->json(AchatCommande::withTrashed()->with(['fournisseur','lignes.produit','depenses'])->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(AchatCommande::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = AchatCommande::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { AchatCommande::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}
