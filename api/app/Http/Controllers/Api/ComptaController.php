<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\ComptaClasses;
use App\Models\ComptaComptes;
use App\Models\ComptaJournaux;
use App\Models\ComptaConfig;
use Illuminate\Http\Request;

class ComptaClassesController extends Controller
{
    public function index()   { return response()->json(ComptaClasses::withTrashed()->with('comptes')->paginate(100)); }
    public function show($id) { return response()->json(ComptaClasses::withTrashed()->with('comptes')->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(ComptaClasses::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = ComptaClasses::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { ComptaClasses::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class ComptaComptesController extends Controller
{
    public function index()   { return response()->json(ComptaComptes::withTrashed()->with('classeComptable')->paginate(200)); }
    public function show($id) { return response()->json(ComptaComptes::withTrashed()->findOrFail($id)); }
    public function store(Request $r)  { return response()->json(ComptaComptes::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = ComptaComptes::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
    public function destroy($id) { ComptaComptes::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class ComptaJournauxController extends Controller
{
    public function index(Request $r)
    {
        $q = ComptaJournaux::withTrashed()->with(['user', 'ecritures.compteComptable']);
        if ($r->filled('enterprise_id')) $q->where('enterprise_id', $r->enterprise_id);
        if ($r->filled('date_from'))     $q->whereDate('date_operation', '>=', $r->date_from);
        if ($r->filled('date_to'))       $q->whereDate('date_operation', '<=', $r->date_to);
        return response()->json($q->latest('date_operation')->paginate(50));
    }

    public function show($id) { return response()->json(ComptaJournaux::withTrashed()->with(['user', 'ecritures.compteComptable'])->findOrFail($id)); }

    public function store(Request $r) { return response()->json(ComptaJournaux::create($r->all()), 201); }

    public function update(Request $r, $id)
    {
        $m = ComptaJournaux::withTrashed()->findOrFail($id);
        $m->update($r->all());
        return response()->json($m);
    }

    public function destroy($id) { ComptaJournaux::findOrFail($id)->delete(); return response()->json(['message' => 'Supprimé.']); }
}

class ComptaConfigController extends Controller
{
    public function show($id) { return response()->json(ComptaConfig::withTrashed()->findOrFail($id)); }
    public function byPos($pos_id) { return response()->json(ComptaConfig::where('pos_id', $pos_id)->firstOrFail()); }
    public function store(Request $r) { return response()->json(ComptaConfig::create($r->all()), 201); }
    public function update(Request $r, $id) { $m = ComptaConfig::withTrashed()->findOrFail($id); $m->update($r->all()); return response()->json($m); }
}
